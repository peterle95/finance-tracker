package com.peterle95.financetracker.data

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import androidx.room.withTransaction
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.jsonObject

class FinanceRepository(context: Context) {
    private val appContext = context.applicationContext
    private val database = FinanceDatabase.get(appContext)
    private val transactionDao = database.transactionDao()
    private val metadataDao = database.metadataDao()
    private val settingsDataStore = SettingsDataStore(appContext)
    private val json = Json

    val transactions: Flow<List<FinanceTransaction>> =
        transactionDao.observeAll().map { rows -> rows.map { it.toDomain() } }

    val categories: Flow<CategoryState> = settingsDataStore.categories

    val budgetSettings: Flow<JsonObject> = metadataDao.observe().map { metadata ->
        metadata?.budgetSettingsJson?.decodeJsonObject() ?: buildJsonObject {}
    }

    suspend fun addTransaction(
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
    ) {
        val now = System.currentTimeMillis()
        transactionDao.insert(
            TransactionEntity(
                exportId = (now / 1000.0).toString(),
                type = type.label,
                date = date,
                amount = amount,
                category = category,
                description = description,
                behaviorDate = null,
                extraJson = "{}",
                createdAt = now,
                updatedAt = now,
            ),
        )
    }

    suspend fun deleteTransaction(localId: Long) {
        transactionDao.deleteById(localId)
    }

    suspend fun setCategories(type: TransactionType, categories: List<String>) {
        settingsDataStore.setCategories(type, categories)
    }

    suspend fun importFromUri(contentResolver: ContentResolver, uri: Uri) {
        val content = contentResolver.openInputStream(uri)?.bufferedReader()?.use { it.readText() }
            ?: error("Could not read selected file.")
        val parsed = FinanceJsonCodec.parse(content)
        database.withTransaction {
            transactionDao.clear()
            metadataDao.clear()
            metadataDao.upsert(
                FinanceMetadataEntity(
                    budgetSettingsJson = json.encodeToString(JsonObject.serializer(), parsed.budgetSettings),
                    topLevelExtraJson = json.encodeToString(JsonObject.serializer(), parsed.topLevelExtra),
                ),
            )
            if (parsed.transactions.isNotEmpty()) transactionDao.insertAll(parsed.transactions)
        }
        settingsDataStore.replaceCategories(parsed.categories.expenses, parsed.categories.incomes)
    }

    suspend fun exportToUri(contentResolver: ContentResolver, uri: Uri) {
        val content = exportJson()
        contentResolver.openOutputStream(uri, "wt")?.bufferedWriter()?.use { it.write(content) }
            ?: error("Could not write selected file.")
    }

    suspend fun exportJson(): String =
        FinanceJsonCodec.encode(
            transactions = transactionDao.getAll(),
            metadata = metadataDao.get(),
            categories = settingsDataStore.categories.first(),
        )

    private fun String?.decodeJsonObject(): JsonObject =
        runCatching {
            if (isNullOrBlank()) buildJsonObject {} else json.parseToJsonElement(this).jsonObject
        }.getOrDefault(buildJsonObject {})
}
