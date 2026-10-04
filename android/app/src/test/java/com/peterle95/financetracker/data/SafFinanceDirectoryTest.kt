package com.peterle95.financetracker.data

import android.content.ContentProvider
import android.content.ContentValues
import android.content.pm.ProviderInfo
import android.database.Cursor
import android.database.MatrixCursor
import android.net.Uri
import android.os.Bundle
import android.os.ParcelFileDescriptor
import android.provider.DocumentsContract
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.flow.first
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.robolectric.shadows.ShadowContentResolver
import java.io.File
import java.io.FileNotFoundException
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], manifest = Config.NONE)
class SafFinanceDirectoryTest {
    @get:Rule val temporaryFolder = TemporaryFolder()
    private lateinit var provider: TestDocumentsProvider
    private lateinit var directory: SafFinanceDirectory

    @Before
    fun setUp() {
        provider = TestDocumentsProvider(temporaryFolder.root)
        provider.attachInfo(RuntimeEnvironment.getApplication(), ProviderInfo().apply {
            authority = "finance.test"
            exported = true
            grantUriPermissions = true
            readPermission = "android.permission.MANAGE_DOCUMENTS"
            writePermission = "android.permission.MANAGE_DOCUMENTS"
        })
        ShadowContentResolver.registerProviderInternal("finance.test", provider)
        directory = SafFinanceDirectory(
            RuntimeEnvironment.getApplication().contentResolver,
            DocumentsContract.buildTreeDocumentUri("finance.test", "root"),
        )
        provider.replace("categories.json", "{}")
        provider.replace("budget.json", "{}")
    }

    @Test
    fun oneListingServesReadsWritesCreatesAndDeletes() = runBlocking {
        assertEquals(setOf("categories.json", "budget.json"), directory.listFiles().toSet())
        assertEquals(1, provider.queries)
        provider.queries = 0
        repeat(3) { assertEquals("{}", directory.readText("budget.json")) }
        directory.writeText("budget.json", "{\"goal\":5}")
        assertEquals("{\"goal\":5}", directory.readText("budget.json"))
        directory.writeText("loans.json", "[]")
        assertEquals("[]", directory.readText("loans.json"))
        directory.delete("loans.json")
        assertNull(directory.readText("loans.json"))
        assertEquals(0, provider.queries)
    }

    @Test
    fun staleIdsRecoverAfterExternalReplacementAndDeletion() = runBlocking {
        directory.listFiles()
        provider.replace("budget.json", "{\"external\":true}")
        provider.queries = 0
        assertEquals("{\"external\":true}", directory.readText("budget.json"))
        assertEquals(1, provider.queries)

        provider.replace("budget.json", "{}")
        directory.writeText("budget.json", "{\"saved\":true}")
        assertEquals("{\"saved\":true}", directory.readText("budget.json"))
        assertEquals(2, provider.queries)

        provider.replace("budget.json", "{}")
        directory.delete("budget.json")
        assertNull(directory.readText("budget.json"))
        assertEquals(3, provider.queries)

        provider.remove("categories.json")
        assertNull(directory.readText("categories.json"))
        provider.replace("categories.json", "{\"new\":true}")
        assertTrue("categories.json" in directory.listFiles())
        assertEquals("{\"new\":true}", directory.readText("categories.json"))
    }

    @Test
    fun failedListingAndPermissionErrorsAreNotMissingFiles() = runBlocking {
        directory.listFiles()
        provider.nullCursor = true
        assertEquals("Could not list finance directory.", runCatching { directory.listFiles() }.exceptionOrNull()?.message)
        provider.nullCursor = false
        provider.denyReads = true
        provider.queries = 0
        assertTrue(runCatching { directory.readText("budget.json") }.exceptionOrNull() is SecurityException)
        assertEquals(0, provider.queries)
    }

    @Test
    fun repositoryCoalescesRefreshesAndRetainsLastGoodDataOnFailure() = runBlocking {
        val repository = repositoryWithFiles()
        val entered = CountDownLatch(1)
        val release = CountDownLatch(1)
        provider.beforeQuery = {
            entered.countDown()
            check(release.await(10, TimeUnit.SECONDS))
        }
        val first = async(start = CoroutineStart.UNDISPATCHED) { repository.reloadConnectedFile() }
        try {
            assertTrue(entered.await(10, TimeUnit.SECONDS))
            assertTrue(repository.syncStatus.first().isLoading)
            val second = async(start = CoroutineStart.UNDISPATCHED) { repository.reloadConnectedFile() }
            release.countDown()
            first.await()
            second.await()
        } finally {
            release.countDown()
        }
        assertEquals(1, provider.queries)
        val lastGood = repository.transactions.first()
        assertEquals("one", lastGood.single().exportId)
        assertEquals(false, repository.syncStatus.first().isLoading)

        provider.beforeQuery = { error("Provider unavailable") }
        assertTrue(runCatching { repository.reloadConnectedFile() }.isFailure)
        assertEquals(lastGood, repository.transactions.first())
        assertEquals("Provider unavailable", repository.syncStatus.first().lastError)
        assertEquals(false, repository.syncStatus.first().isLoading)

        provider.beforeQuery = null
        provider.replace("budget.json", "[]")
        assertTrue(runCatching { repository.reloadConnectedFile() }.isFailure)
        repository.addTransaction(TransactionType.Expense, "2026-10-04", 7.0, "Food", "Saved")
        assertEquals("budget.json is missing or is not a JSON object.", repository.syncStatus.first().lastError)
        provider.replace("budget.json", "{}")
        repository.reloadConnectedFile()
        assertEquals(2, repository.transactions.first().size)
        assertNull(repository.syncStatus.first().lastError)
    }

    @Test
    fun savingAfterColdLoadRecoveryClearsTheObsoleteRefreshError() = runBlocking {
        val repository = repositoryWithFiles()
        provider.replace("budget.json", "[]")
        assertTrue(runCatching { repository.reloadConnectedFile() }.isFailure)
        provider.replace("budget.json", "{}")

        repository.addTransaction(TransactionType.Expense, "2026-10-04", 7.0, "Food", "Saved")

        assertEquals(2, repository.transactions.first().size)
        assertNull(repository.syncStatus.first().lastError)
        assertNotNull(repository.syncStatus.first().lastLoadedAt)
    }

    private suspend fun repositoryWithFiles(): FinanceRepository {
        provider.replace("categories.json", """{"Expense":[{"name":"Food","file_key":"food"}],"Income":[]}""")
        provider.replace("net_worth.json", "{}")
        provider.replace("preferences.json", "{}")
        provider.replace("loans.json", "[]")
        provider.replace("savings_goals.json", "[]")
        provider.replace("transactions_expense_food.json", """[{"id":"one","date":"2026-10-04","amount":5,"category":"Food"}]""")
        val context = RuntimeEnvironment.getApplication()
        SettingsDataStore(context).setSyncedTreeUri(DocumentsContract.buildTreeDocumentUri("finance.test", "root").toString())
        return FinanceRepository(context)
    }

    class TestDocumentsProvider(private val root: File) : ContentProvider() {
        private val entries = linkedMapOf<String, String>()
        private var nextId = 0
        var queries = 0
        var beforeQuery: (() -> Unit)? = null
        var nullCursor = false
        var denyReads = false

        fun replace(name: String, content: String) {
            remove(name)
            val id = "file-${nextId++}"
            entries[name] = id
            File(root, id).writeText(content)
        }

        fun remove(name: String) {
            entries.remove(name)?.let { File(root, it).delete() }
        }

        override fun onCreate() = true
        override fun query(uri: Uri, projection: Array<out String>?, selection: String?, selectionArgs: Array<out String>?, sortOrder: String?): Cursor? {
            queries++
            beforeQuery?.invoke()
            if (nullCursor) return null
            return cursor(projection).apply { entries.forEach { (name, id) -> addDocument(name, id) } }
        }

        override fun openFile(uri: Uri, mode: String): ParcelFileDescriptor {
            if (denyReads) throw SecurityException("Permission revoked")
            val documentId = DocumentsContract.getDocumentId(uri)
            if (documentId !in entries.values) throw FileNotFoundException(documentId)
            return ParcelFileDescriptor.open(File(root, documentId), ParcelFileDescriptor.parseMode(mode))
        }

        override fun call(method: String, arg: String?, extras: Bundle?): Bundle {
            val uri = extras!!.getParcelable("uri", Uri::class.java)!!
            return when (method) {
                "android:createDocument" -> {
                    val name = extras.getString(DocumentsContract.Document.COLUMN_DISPLAY_NAME)!!
                    replace(name, "")
                    Bundle().apply { putParcelable("uri", DocumentsContract.buildDocumentUriUsingTree(uri, entries.getValue(name))) }
                }
                "android:deleteDocument" -> {
                    val id = DocumentsContract.getDocumentId(uri)
                    val name = entries.entries.firstOrNull { it.value == id }?.key ?: throw FileNotFoundException(id)
                    remove(name)
                    Bundle()
                }
                else -> error(method)
            }
        }

        override fun getType(uri: Uri) = "application/json"
        override fun insert(uri: Uri, values: ContentValues?): Uri? = error("Unsupported")
        override fun delete(uri: Uri, selection: String?, selectionArgs: Array<out String>?) = error("Unsupported")
        override fun update(uri: Uri, values: ContentValues?, selection: String?, selectionArgs: Array<out String>?) = error("Unsupported")

        private fun cursor(projection: Array<out String>?) = MatrixCursor(projection ?: arrayOf(
            DocumentsContract.Document.COLUMN_DOCUMENT_ID,
            DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            DocumentsContract.Document.COLUMN_MIME_TYPE,
        ))

        private fun MatrixCursor.addDocument(name: String, id: String) {
            addRow(columnNames.map {
                when (it) {
                    DocumentsContract.Document.COLUMN_DOCUMENT_ID -> id
                    DocumentsContract.Document.COLUMN_DISPLAY_NAME -> name
                    DocumentsContract.Document.COLUMN_MIME_TYPE -> "application/json"
                    else -> null
                }
            })
        }
    }
}
