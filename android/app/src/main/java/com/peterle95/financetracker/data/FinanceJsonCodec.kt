package com.peterle95.financetracker.data

import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.buildJsonArray
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.util.UUID

data class FinanceDocument(
    val records: List<FinanceRecord> = emptyList(),
    val budgetSettings: JsonObject = buildJsonObject {},
    val categories: CategoryState = CategoryState(),
    val topLevelExtra: JsonObject = buildJsonObject {},
) {
    val transactions: List<FinanceTransaction>
        get() = records.map { it.transaction }

    companion object {
        fun empty() = FinanceDocument()
    }
}

data class FinanceRecord(
    val transaction: FinanceTransaction,
    val extraJson: JsonObject = buildJsonObject {},
)

object FinanceJsonCodec {
    private val json = Json {
        prettyPrint = true
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    private val rootKeys = setOf("expenses", "incomes", "budget_settings", "categories")
    private val transactionKeys = setOf("id", "date", "amount", "category", "description", "behavior_date")

    fun parse(content: String): FinanceDocument {
        val root = json.parseToJsonElement(content).jsonObject
        val expenses = root["expenses"].arrayOrEmpty()
            .mapNotNullIndexed { index, element ->
                (element as? JsonObject)?.toRecord(TransactionType.Expense, index)
            }
        val incomes = root["incomes"].arrayOrEmpty()
            .mapNotNullIndexed { index, element ->
                (element as? JsonObject)?.toRecord(TransactionType.Income, index)
            }

        return FinanceDocument(
            records = expenses + incomes,
            budgetSettings = root["budget_settings"] as? JsonObject ?: buildJsonObject {},
            categories = parseCategories(root["categories"] as? JsonObject),
            topLevelExtra = JsonObject(root.filterKeys { it !in rootKeys }),
        )
    }

    fun encode(document: FinanceDocument): String {
        val root = buildJsonObject {
            document.topLevelExtra.forEach { (key, value) ->
                if (key !in rootKeys) put(key, value)
            }
            put(
                "expenses",
                JsonArray(
                    document.records
                        .filter { it.transaction.type == TransactionType.Expense }
                        .map { it.toJsonObject() },
                ),
            )
            put(
                "incomes",
                JsonArray(
                    document.records
                        .filter { it.transaction.type == TransactionType.Income }
                        .map { it.toJsonObject() },
                ),
            )
            put("budget_settings", document.budgetSettings)
            put("categories", buildJsonObject {
                put("Expense", document.categories.expenses.toJsonArray())
                put("Income", document.categories.incomes.toJsonArray())
            })
        }
        return json.encodeToString(JsonObject.serializer(), root)
    }

    fun addTransaction(
        document: FinanceDocument,
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        id: String = UUID.randomUUID().toString(),
    ): FinanceDocument {
        val transaction = FinanceTransaction(
            uiKey = id,
            exportId = id,
            type = type,
            date = date,
            amount = amount,
            category = category,
            description = description,
            behaviorDate = null,
        )
        return document.copy(records = document.records + FinanceRecord(transaction))
    }

    fun deleteTransactionByExportId(document: FinanceDocument, exportId: String): FinanceDocument {
        require(exportId.isNotBlank()) { "This transaction has no JSON id and cannot be deleted from Android." }
        return document.copy(records = document.records.filterNot { it.transaction.exportId == exportId })
    }

    fun updateCategories(
        document: FinanceDocument,
        type: TransactionType,
        categories: List<String>,
    ): FinanceDocument {
        val normalized = categories.normalized(
            if (type == TransactionType.Expense) CategoryDefaults.expense else CategoryDefaults.income,
        )
        return document.copy(
            categories = if (type == TransactionType.Expense) {
                document.categories.copy(expenses = normalized)
            } else {
                document.categories.copy(incomes = normalized)
            },
        )
    }

    private fun JsonObject.toRecord(type: TransactionType, index: Int): FinanceRecord {
        val extra = JsonObject(filterKeys { it !in transactionKeys })
        val exportId = this["id"]?.jsonPrimitiveOrNull()?.contentOrNull
        val date = this["date"].stringOrEmpty()
        val category = this["category"].stringOrEmpty()
        val description = this["description"].stringOrEmpty()
        val uiKey = exportId ?: "${type.label}-$index-$date-$category-$description"
        return FinanceRecord(
            transaction = FinanceTransaction(
                uiKey = uiKey,
                exportId = exportId,
                type = type,
                date = date,
                amount = this["amount"]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0,
                category = category,
                description = description,
                behaviorDate = this["behavior_date"]?.jsonPrimitiveOrNull()?.contentOrNull,
            ),
            extraJson = extra,
        )
    }

    private fun FinanceRecord.toJsonObject(): JsonObject =
        buildJsonObject {
            extraJson.forEach { (key, value) ->
                if (key !in transactionKeys) put(key, value)
            }
            transaction.exportId?.let { put("id", it) }
            put("date", transaction.date)
            put("amount", transaction.amount)
            put("category", transaction.category)
            put("description", transaction.description)
            transaction.behaviorDate?.takeIf { it.isNotBlank() }?.let { put("behavior_date", it) }
        }

    private fun parseCategories(categories: JsonObject?): CategoryState =
        CategoryState(
            expenses = categories?.get("Expense").stringListOrDefault(CategoryDefaults.expense),
            incomes = categories?.get("Income").stringListOrDefault(CategoryDefaults.income),
        )

    private fun JsonElement?.arrayOrEmpty(): JsonArray =
        runCatching { this?.jsonArray }.getOrNull() ?: buildJsonArray {}

    private fun JsonElement?.stringListOrDefault(defaults: List<String>): List<String> =
        runCatching {
            this?.jsonArray
                ?.mapNotNull { it.jsonPrimitive.contentOrNull?.trim() }
                ?.filter { it.isNotEmpty() }
                ?.distinctBy { it.lowercase() }
                ?.ifEmpty { defaults }
        }.getOrNull() ?: defaults

    private fun List<String>.normalized(defaults: List<String>): List<String> =
        map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinctBy { it.lowercase() }
            .ifEmpty { defaults }

    private fun List<String>.toJsonArray(): JsonArray =
        JsonArray(map { JsonPrimitive(it) })

    private fun JsonElement?.stringOrEmpty(): String =
        if (this == null || this is JsonNull) "" else jsonPrimitiveOrNull()?.contentOrNull.orEmpty()

    private fun JsonElement.jsonPrimitiveOrNull() =
        runCatching { jsonPrimitive }.getOrNull()
}

private inline fun <T, R : Any> Iterable<T>.mapNotNullIndexed(transform: (Int, T) -> R?): List<R> {
    val destination = ArrayList<R>()
    forEachIndexed { index, item ->
        transform(index, item)?.let(destination::add)
    }
    return destination
}
