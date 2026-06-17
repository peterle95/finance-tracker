package com.peterle95.financetracker.domain

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeParseException

object FinanceAggregator {
    fun buildInsightsSummary(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        endMonth: YearMonth = YearMonth.now(),
        monthsBack: Int = 1,
    ): InsightsSummary {
        val months = (monthsBack - 1 downTo 0).map { endMonth.minusMonths(it.toLong()).toString() }
        val monthSet = months.toSet()
        val expenses = transactions.filter {
            it.type == TransactionType.Expense && it.date.take(7) in monthSet
        }
        val incomes = transactions.filter {
            it.type == TransactionType.Income && it.date.take(7) in monthSet
        }

        val expenseTotals = totalsByCategory(expenses)
        val incomeTotals = totalsByCategory(incomes)
        val totalFlexibleExpenses = expenseTotals.values.sum()
        val totalFlexibleIncome = incomeTotals.values.sum()

        var totalFixedCosts = 0.0
        var totalBaseIncome = 0.0

        months.forEach { month ->
            activeFixedCosts(budgetSettings, month).forEach { fixedCost ->
                val amount = fixedCost.numberValue("amount")
                totalFixedCosts += amount
                val description = fixedCost.stringValue("description")
                    ?: fixedCost.stringValue("desc")
                    ?: "Untitled"
                val category = "Fixed: $description"
                expenseTotals[category] = (expenseTotals[category] ?: 0.0) + amount
            }

            val baseIncome = activeMonthlyIncome(budgetSettings, month)
            if (baseIncome > 0.0) {
                totalBaseIncome += baseIncome
                incomeTotals["Base Monthly Income"] =
                    (incomeTotals["Base Monthly Income"] ?: 0.0) + baseIncome
            }
        }

        val totalExpenses = totalFlexibleExpenses + totalFixedCosts
        val totalIncome = totalFlexibleIncome + totalBaseIncome

        return InsightsSummary(
            months = months,
            totals = FinanceTotals(
                income = totalIncome,
                expenses = totalExpenses,
                net = totalIncome - totalExpenses,
                fixedCosts = totalFixedCosts,
                baseIncome = totalBaseIncome,
                flexibleExpenses = totalFlexibleExpenses,
                flexibleIncome = totalFlexibleIncome,
            ),
            expenseCategories = expenseTotals.toSortedMap(),
            incomeCategories = incomeTotals.toSortedMap(),
            transactionCounts = TransactionCounts(
                flexibleExpenses = expenses.size,
                flexibleIncomes = incomes.size,
            ),
        )
    }

    fun buildDashboardSummary(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        currentMonth: YearMonth = YearMonth.now(),
    ): DashboardSummary {
        val summary = buildInsightsSummary(transactions, budgetSettings, currentMonth, monthsBack = 1)
        return DashboardSummary(
            currentMonth = currentMonth.toString(),
            income = summary.totals.income,
            expenses = summary.totals.expenses,
            net = summary.totals.net,
            topExpenseCategories = summary.expenseCategories
                .filterKeys { !it.startsWith("Fixed: ") }
                .toList()
                .sortedByDescending { it.second }
                .take(5),
            balanceEstimate = balanceEstimate(budgetSettings),
        )
    }

    private fun totalsByCategory(rows: List<FinanceTransaction>): MutableMap<String, Double> {
        val totals = mutableMapOf<String, Double>()
        rows.forEach { row ->
            val category = row.category.ifBlank { "Uncategorized" }
            totals[category] = (totals[category] ?: 0.0) + row.amount
        }
        return totals
    }

    private fun activeFixedCosts(budgetSettings: JsonObject, month: String): List<JsonObject> {
        val costs = budgetSettings["fixed_costs"] as? JsonArray ?: return emptyList()
        return costs.mapNotNull { it as? JsonObject }
            .filter { isActiveForMonth(it, month) }
    }

    private fun activeMonthlyIncome(budgetSettings: JsonObject, month: String): Double {
        val income = budgetSettings["monthly_income"] ?: return 0.0
        income.jsonPrimitiveOrNull()?.doubleOrNull?.let { return it }
        val rows = income as? JsonArray ?: return 0.0
        return rows.mapNotNull { it as? JsonObject }
            .filter { isActiveForMonth(it, month) }
            .sumOf { it.numberValue("amount") }
    }

    private fun isActiveForMonth(row: JsonObject, month: String): Boolean {
        val yearMonth = try {
            YearMonth.parse(month)
        } catch (_: DateTimeParseException) {
            return true
        }
        val monthStart = yearMonth.atDay(1)
        val monthEnd = yearMonth.atEndOfMonth()
        val start = row.stringValue("start_date")?.parseIsoDateOrNull() ?: LocalDate.of(2000, 1, 1)
        val end = row["end_date"].stringOrNull()?.parseIsoDateOrNull()
        return !start.isAfter(monthEnd) && (end == null || !end.isBefore(monthStart))
    }

    private fun balanceEstimate(budgetSettings: JsonObject): Double? {
        val keys = listOf(
            "bank_account_balance",
            "wallet_balance",
            "savings_balance",
            "investment_balance",
            "money_lent_balance",
        )
        val available = keys.filter { budgetSettings.containsKey(it) }
        if (available.isEmpty()) return null
        return available.sumOf { budgetSettings.numberValue(it) }
    }

    private fun JsonObject.numberValue(key: String): Double =
        this[key]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0

    private fun JsonObject.stringValue(key: String): String? = this[key].stringOrNull()

    private fun JsonElement?.stringOrNull(): String? =
        if (this == null || this is JsonNull) null else jsonPrimitiveOrNull()?.contentOrNull

    private fun JsonElement.jsonPrimitiveOrNull() = runCatching { jsonPrimitive }.getOrNull()

    private fun String.parseIsoDateOrNull(): LocalDate? =
        runCatching { LocalDate.parse(this) }.getOrNull()
}
