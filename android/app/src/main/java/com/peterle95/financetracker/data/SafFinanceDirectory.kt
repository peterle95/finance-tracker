package com.peterle95.financetracker.data

import android.content.ContentResolver
import android.net.Uri
import android.provider.DocumentsContract
import java.nio.charset.StandardCharsets

class SafFinanceDirectory(
    private val resolver: ContentResolver,
    private val treeUri: Uri,
) : FinanceDirectory {
    private var financeDirectoryId: String? = null

    override suspend fun listFiles(): List<String> {
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(
            treeUri,
            directoryId(),
        )
        return resolver.query(
            children,
            arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME),
            null,
            null,
            null,
        )?.use { cursor ->
            val nameColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
            buildList {
                while (cursor.moveToNext()) add(cursor.getString(nameColumn))
            }
        }.orEmpty()
    }

    override suspend fun readText(name: String): String? {
        val uri = find(name) ?: return null
        return resolver.openInputStream(uri)?.bufferedReader(StandardCharsets.UTF_8)?.use { it.readText() }
            ?: error("Could not read $name.")
    }

    override suspend fun writeText(name: String, content: String) {
        val uri = find(name) ?: DocumentsContract.createDocument(
            resolver,
            DocumentsContract.buildDocumentUriUsingTree(treeUri, directoryId()),
            "application/json",
            name,
        ) ?: error("Could not create $name.")
        resolver.openOutputStream(uri, "wt")?.bufferedWriter(StandardCharsets.UTF_8)?.use {
            it.write(content)
            it.flush()
        } ?: error("Could not write $name.")
    }

    override suspend fun delete(name: String) {
        find(name)?.let { DocumentsContract.deleteDocument(resolver, it) }
    }

    private fun find(name: String): Uri? {
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(
            treeUri,
            directoryId(),
        )
        return resolver.query(
            children,
            arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
            ),
            null,
            null,
            null,
        )?.use { cursor ->
            val idColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID)
            val nameColumn = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
            var result: Uri? = null
            while (cursor.moveToNext()) {
                if (cursor.getString(nameColumn) == name) {
                    result = DocumentsContract.buildDocumentUriUsingTree(treeUri, cursor.getString(idColumn))
                    break
                }
            }
            result
        }
    }

    private fun directoryId(): String {
        financeDirectoryId?.let { return it }
        val root = DocumentsContract.getTreeDocumentId(treeUri)
        if (hasFinanceMarker(root)) return root.also { financeDirectoryId = it }
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, root)
        val shared = resolver.query(
            children,
            arrayOf(
                DocumentsContract.Document.COLUMN_DOCUMENT_ID,
                DocumentsContract.Document.COLUMN_DISPLAY_NAME,
                DocumentsContract.Document.COLUMN_MIME_TYPE,
            ),
            null,
            null,
            null,
        )?.use { cursor ->
            val id = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DOCUMENT_ID)
            val name = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
            val mime = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_MIME_TYPE)
            var result: String? = null
            while (cursor.moveToNext()) {
                if (cursor.getString(name) == "shared"
                    && cursor.getString(mime) == DocumentsContract.Document.MIME_TYPE_DIR) {
                    result = cursor.getString(id)
                    break
                }
            }
            result
        }
        return (shared?.takeIf(::hasFinanceMarker) ?: root).also { financeDirectoryId = it }
    }

    private fun hasFinanceMarker(documentId: String): Boolean {
        val children = DocumentsContract.buildChildDocumentsUriUsingTree(treeUri, documentId)
        return resolver.query(
            children,
            arrayOf(DocumentsContract.Document.COLUMN_DISPLAY_NAME),
            null,
            null,
            null,
        )?.use { cursor ->
            val name = cursor.getColumnIndexOrThrow(DocumentsContract.Document.COLUMN_DISPLAY_NAME)
            var found = false
            while (cursor.moveToNext()) {
                if (cursor.getString(name) in setOf("categories.json", "finance_data.json")) {
                    found = true
                    break
                }
            }
            found
        } == true
    }
}
