package com.peterle95.financetracker.data

import android.content.ContentResolver
import android.net.Uri
import android.provider.DocumentsContract
import java.io.FileNotFoundException
import java.nio.charset.StandardCharsets

class SafFinanceDirectory(
    private val resolver: ContentResolver,
    private val treeUri: Uri,
) : FinanceDirectory {
    private var financeDirectoryId: String? = null
    private var documents: MutableMap<String, Uri>? = null

    override suspend fun listFiles(): List<String> {
        refreshIndex()
        return documents!!.keys.toList()
    }

    override suspend fun readText(name: String): String? {
        val stream = withDocument(name) { resolver.openInputStream(it) ?: error("Could not read $name.") }
            ?: return null
        return stream.bufferedReader(StandardCharsets.UTF_8).use { it.readText() }
    }

    override suspend fun writeText(name: String, content: String) {
        val stream = withDocument(name, create = true) {
            resolver.openOutputStream(it, "wt") ?: error("Could not write $name.")
        } ?: error("Could not write $name.")
        stream.bufferedWriter(StandardCharsets.UTF_8).use {
            it.write(content)
            it.flush()
        }
    }

    override suspend fun delete(name: String) {
        withDocument(name) {
            if (!DocumentsContract.deleteDocument(resolver, it)) throw FileNotFoundException("Could not delete $name.")
        }
        documents?.remove(name)
    }

    private fun <T> withDocument(name: String, create: Boolean = false, action: (Uri) -> T): T? {
        if (documents == null) refreshIndex()
        val uri = documentUri(name, create) ?: return null
        return try {
            action(uri)
        } catch (error: FileNotFoundException) {
            refreshIndex()
            val replacement = documentUri(name, create) ?: return null
            if (replacement == uri) throw error
            action(replacement)
        }
    }

    private fun documentUri(name: String, create: Boolean): Uri? {
        documents!![name]?.let { return it }
        if (!create) return null
        val uri = DocumentsContract.createDocument(
            resolver,
            DocumentsContract.buildDocumentUriUsingTree(treeUri, financeDirectoryId!!),
            "application/json",
            name,
        ) ?: error("Could not create $name.")
        documents!![name] = uri
        return uri
    }

    private fun refreshIndex() {
        var id = financeDirectoryId ?: DocumentsContract.getTreeDocumentId(treeUri)
        var children = queryChildren(id)
        if (financeDirectoryId == null && !hasFinanceMarker(children)) {
            children["shared"]?.takeIf { it.mimeType == DocumentsContract.Document.MIME_TYPE_DIR }?.let { shared ->
                val sharedChildren = queryChildren(shared.id)
                if (hasFinanceMarker(sharedChildren)) {
                    id = shared.id
                    children = sharedChildren
                }
            }
        }
        financeDirectoryId = id
        documents = children.mapValues { (_, child) ->
            DocumentsContract.buildDocumentUriUsingTree(treeUri, child.id)
        }.toMutableMap()
    }

    private fun queryChildren(id: String): Map<String, ChildDocument> =
        resolver.query(
            DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, id),
            arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE,
            ),
            null,
            null,
            null,
        )?.use { cursor ->
            val idColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID)
            val nameColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
            val mimeColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_MIME_TYPE)
            buildMap {
                while (cursor.moveToNext()) {
                    put(cursor.getString(nameColumn), ChildDocument(cursor.getString(idColumn), cursor.getString(mimeColumn)))
                }
            }
        } ?: error("Could not list finance directory.")

    private fun hasFinanceMarker(children: Map<String, ChildDocument>) =
        "categories.json" in children || "finance_data.json" in children

    private data class ChildDocument(val id: String, val mimeType: String)
}
