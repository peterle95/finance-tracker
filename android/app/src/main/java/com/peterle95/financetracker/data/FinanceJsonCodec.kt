package com.peterle95.financetracker.data

import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.CategoryState
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

data class ParsedFinanceDocument(
    val transactions: List<TransactionEntity>,
    val budgetSettings: JsonObject,
    val categories: CategoryState,
    val topLevelExtra: JsonObject,
)

object FinanceJsonCodec {
    private val json = Json {
        prettyPrint = true
        encodeDefaults = true
        ignoreUnknownKeys = true
    }

    private val rootKeys = setOf("expenses", "incomes", "budget_settings", "categories")
    private val transactionKeys = setOf("id", "date", "amount", "category", "description", "behavior_date")

    fun parse(content: String, nowMillis: Long = System.currentTimeMillis()): ParsedFinanceDocument {
        val root = json.parseToJsonElement(content).jsonObject
        val expenses = root["expenses"].arrayOrEmpty()
            .mapNotNull { it as? JsonObject }
            .map { it.toEntity(TransactionType.Expense, nowMillis) }
        val incomes = root["incomes"].arrayOrEmpty()
            .mapNotNull { it as? JsonObject }
            .map { it.toEntity(TransactionType.Income, nowMillis) }

        return ParsedFinanceDocument(
            transactions = expenses + incomes,
            budgetSettings = root["budget_settings"] as? JsonObject ?: buildJsonObject {},
            categories = parseCategories(root["categories"] as? JsonObject),
            topLevelExtra = JsonObject(root.filterKeys { it !in rootKeys }),
        )
    }

    fun encode(
        transactions: List<TransactionEntity>,
        metadata: FinanceMetadataEntity?,
        categories: CategoryState,
    ): String {
        val expenses = transactions
            .filter { TransactionType.fromLabel(it.type) == TransactionType.Expense }
            .sortedBy { it.date }
            .map { it.toJsonObject() }
        val incomes = transactions
            .filter { TransactionType.fromLabel(it.type) == TransactionType.Income }
            .sortedBy { it.date }
            .map { it.toJsonObject() }

        val extras = metadata?.topLevelExtraJson?.decodeJsonObject() ?: buildJsonObject {}
        val budgetSettings = metadata?.budgetSettingsJson?.decodeJsonObject() ?: buildJsonObject {}
        val root = buildJsonObject {
            extras.forEach { (key, value) ->
                if (key !in rootKeys) put(key, value)
            }
            put("expenses", JsonArray(expenses))
            put("incomes", JsonArray(incomes))
            put("budget_settings", budgetSettings)
            put("categories", buildJsonObject {
                put("Expense", categories.expenses.toJsonArray())
                put("Income", categories.incomes.toJsonArray())
            })
        }
        return json.encodeToString(JsonObject.serializer(), root)
    }

    private fun JsonObject.toEntity(type: TransactionType, nowMillis: Long): TransactionEntity {
        val extra = JsonObject(filterKeys { it !in transactionKeys })
        val exportId = this["id"]?.jsonPrimitiveOrNull()?.contentOrNull
        return TransactionEntity(
            exportId = exportId,
            type = type.label,
            date = this["date"].stringOrEmpty(),
            amount = this["amount"]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0,
            category = this["category"].stringOrEmpty(),
            description = this["description"].stringOrEmpty(),
            behaviorDate = this["behavior_date"]?.jsonPrimitiveOrNull()?.contentOrNull,
            extraJson = json.encodeToString(JsonObject.serializer(), extra),
            createdAt = nowMillis,
            updatedAt = nowMillis,
        )
    }

    private fun TransactionEntity.toJsonObject(): JsonObject {
        val extras = extraJson.decodeJsonObject()
        return buildJsonObject {
            extras.forEach { (key, value) ->
                if (key !in transactionKeys) put(key, value)
            }
            exportId?.let { put("id", it) }
            put("date", date)
            put("amount", amount)
            put("category", category)
            put("description", description)
            behaviorDate?.takeIf { it.isNotBlank() }?.let { put("behavior_date", it) }
        }
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

    private fun List<String>.toJsonArray(): JsonArray =
        JsonArray(map { JsonPrimitive(it) })

    private fun String?.decodeJsonObject(): JsonObject =
        runCatching {
            if (isNullOrBlank()) buildJsonObject {} else json.parseToJsonElement(this).jsonObject
        }.getOrDefault(buildJsonObject {})

    private fun JsonElement?.stringOrEmpty(): String =
        if (this == null || this is JsonNull) "" else jsonPrimitiveOrNull()?.contentOrNull.orEmpty()

    private fun JsonElement.jsonPrimitiveOrNull() =
        runCatching { jsonPrimitive }.getOrNull()
}
