package com.peterle95.financetracker.domain

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

object InsightsJson {
    private val json = Json { prettyPrint = true }

    fun encode(summary: InsightsSummary): String {
        val element = buildJsonObject {
            put("months", kotlinx.serialization.json.JsonArray(summary.months.map { kotlinx.serialization.json.JsonPrimitive(it) }))
            put("totals", buildJsonObject {
                put("income", summary.totals.income)
                put("expenses", summary.totals.expenses)
                put("net", summary.totals.net)
                put("fixed_costs", summary.totals.fixedCosts)
                put("base_income", summary.totals.baseIncome)
                put("flexible_expenses", summary.totals.flexibleExpenses)
                put("flexible_income", summary.totals.flexibleIncome)
            })
            put("expense_categories", summary.expenseCategories.toJsonObject())
            put("income_categories", summary.incomeCategories.toJsonObject())
            put("transaction_counts", buildJsonObject {
                put("flexible_expenses", summary.transactionCounts.flexibleExpenses)
                put("flexible_incomes", summary.transactionCounts.flexibleIncomes)
            })
        }
        return json.encodeToString(kotlinx.serialization.json.JsonObject.serializer(), element)
    }

    private fun Map<String, Double>.toJsonObject() = buildJsonObject {
        forEach { (key, value) -> put(key, value) }
    }
}
