package com.peterle95.financetracker.data

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.OpenableColumns
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.FixedCost
import com.peterle95.financetracker.domain.IncomeSource
import com.peterle95.financetracker.domain.Loan
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class FinanceRepository(context: Context) {
    private val appContext = context.applicationContext
    private val contentResolver = appContext.contentResolver
    private val settingsDataStore = SettingsDataStore(appContext)
    private val mutex = Mutex()
    private val fileStore = FinanceJsonFileStore(
        readText = { readConnectedText() },
        writeText = { writeConnectedText(it) },
    )
    private val _syncStatus = MutableStateFlow(SyncedFileStatus())

    val transactions: Flow<List<FinanceTransaction>> =
        fileStore.document.map { it.transactions }

    val categories: Flow<CategoryState> =
        fileStore.document.map { it.categories }

    val budgetSettings: Flow<JsonObject> =
        fileStore.document.map { it.budgetSettings }

    val budgetSettingsModel: Flow<BudgetSettings> =
        fileStore.document.map { it.budgetSettingsModel }

    val syncStatus: Flow<SyncedFileStatus> = _syncStatus

    suspend fun loadConfiguredFileIfAny() {
        val uri = configuredUriOrNull()
        if (uri == null) {
            _syncStatus.value = SyncedFileStatus()
            return
        }
        reloadConnectedFile()
    }

    suspend fun connectSyncedFile(uri: Uri) {
        require(uri.scheme == ContentResolver.SCHEME_CONTENT) {
            "Choose finance_data.json through Android's file picker so the app receives a content URI."
        }
        val flags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
        contentResolver.takePersistableUriPermission(uri, flags)
        settingsDataStore.setSyncedFileUri(uri.toString())
        reloadConnectedFile()
    }

    suspend fun reloadConnectedFile() = mutex.withLock {
        val uri = requireConfiguredUri()
        runCatching {
            fileStore.reload()
        }.onSuccess {
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastLoadedAt = nowText(),
                lastError = null,
            )
        }.onFailure { error ->
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastError = error.message ?: "Could not reload synced file.",
            )
            throw error
        }
    }

    suspend fun addTransaction(
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        behaviorDate: String? = null,
    ) = mutateConnectedFile {
        FinanceJsonCodec.addTransaction(
            document = it,
            type = type,
            date = date,
            amount = amount,
            category = category,
            description = description,
            behaviorDate = behaviorDate,
        )
    }

    suspend fun deleteTransaction(exportId: String) = mutateConnectedFile {
        FinanceJsonCodec.deleteTransactionByExportId(it, exportId)
    }

    suspend fun setCategories(type: TransactionType, categories: List<String>) = mutateConnectedFile {
        FinanceJsonCodec.updateCategories(it, type, categories)
    }

    suspend fun updateBalances(
        bank: Double,
        wallet: Double,
        savings: Double,
        investments: Double,
    ) = mutateConnectedFile {
        val latestBalances = it.budgetSettingsModel.balances
        FinanceJsonCodec.updateBalances(
            it,
            latestBalances.copy(
                bankAccount = bank,
                wallet = wallet,
                savings = savings,
                investments = investments,
                hasAnyBalanceField = true,
            ),
        )
    }

    suspend fun setDailySavingsGoal(amount: Double) = mutateConnectedFile {
        FinanceJsonCodec.setDailySavingsGoal(it, amount)
    }

    suspend fun addIncomeSource(source: IncomeSource) = mutateConnectedFile {
        FinanceJsonCodec.addIncomeSource(it, source)
    }

    suspend fun updateIncomeSource(key: String, source: IncomeSource) = mutateConnectedFile {
        FinanceJsonCodec.updateIncomeSource(it, key, source)
    }

    suspend fun archiveIncomeSource(key: String, endDate: String) = mutateConnectedFile {
        FinanceJsonCodec.archiveIncomeSource(it, key, endDate)
    }

    suspend fun deleteIncomeSource(key: String) = mutateConnectedFile {
        FinanceJsonCodec.deleteIncomeSource(it, key)
    }

    suspend fun addFixedCost(cost: FixedCost) = mutateConnectedFile {
        FinanceJsonCodec.addFixedCost(it, cost)
    }

    suspend fun updateFixedCost(key: String, cost: FixedCost) = mutateConnectedFile {
        FinanceJsonCodec.updateFixedCost(it, key, cost)
    }

    suspend fun archiveFixedCost(key: String, endDate: String) = mutateConnectedFile {
        FinanceJsonCodec.archiveFixedCost(it, key, endDate)
    }

    suspend fun deleteFixedCost(key: String) = mutateConnectedFile {
        FinanceJsonCodec.deleteFixedCost(it, key)
    }

    suspend fun addLoan(loan: Loan) = mutateConnectedFile {
        FinanceJsonCodec.addLoan(it, loan)
    }

    suspend fun updateLoan(key: String, loan: Loan) = mutateConnectedFile {
        FinanceJsonCodec.updateLoan(it, key, loan)
    }

    suspend fun returnLoan(key: String) = mutateConnectedFile {
        FinanceJsonCodec.returnLoan(it, key)
    }

    suspend fun recordAssetSnapshot(date: String, note: String) = mutateConnectedFile {
        FinanceJsonCodec.recordAssetSnapshot(it, date, note)
    }

    suspend fun deleteAssetSnapshot(date: String) = mutateConnectedFile {
        FinanceJsonCodec.deleteAssetSnapshot(it, date)
    }

    private suspend fun mutateConnectedFile(transform: (FinanceDocument) -> FinanceDocument) = mutex.withLock {
        val uri = requireConfiguredUri()
        runCatching {
            fileStore.mutate(transform)
        }.onSuccess {
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastLoadedAt = nowText(),
                lastWrittenAt = nowText(),
                lastError = null,
            )
        }.onFailure { error ->
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastError = error.message ?: "Could not write synced file.",
            )
            throw error
        }
    }

    private suspend fun readConnectedText(): String {
        val uri = requireConfiguredUri()
        return contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
            ?: error("Could not read connected finance_data.json.")
    }

    private suspend fun writeConnectedText(content: String) {
        val uri = requireConfiguredUri()
        contentResolver.openOutputStream(uri, "wt")?.bufferedWriter()?.use { it.write(content) }
            ?: error("Could not write connected finance_data.json.")
    }

    private suspend fun configuredUriOrNull(): Uri? =
        settingsDataStore.syncedFileUri.first()?.let(Uri::parse)

    private suspend fun requireConfiguredUri(): Uri =
        configuredUriOrNull() ?: error("Connect a synced finance_data.json file in Settings first.")

    private fun displayName(uri: Uri): String =
        runCatching {
            contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
                val index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (cursor.moveToFirst() && index >= 0) cursor.getString(index) else null
            }
        }.getOrNull() ?: uri.lastPathSegment ?: "finance_data.json"

    private fun nowText(): String =
        LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
}
