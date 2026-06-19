package com.peterle95.financetracker.domain

import kotlinx.serialization.json.JsonObject
import java.time.YearMonth

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

        val settings = BudgetSettings.fromJson(budgetSettings)
        var totalFixedCosts = 0.0
        var totalBaseIncome = 0.0

        months.forEach { month ->
            BudgetMath.activeFixedCosts(settings, month).forEach { fixedCost ->
                totalFixedCosts += fixedCost.amount
                val category = "Fixed: ${fixedCost.description.ifBlank { "Untitled" }}"
                expenseTotals[category] = (expenseTotals[category] ?: 0.0) + fixedCost.amount
            }

            val baseIncome = BudgetMath.activeMonthlyIncome(settings, month)
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
        val settings = BudgetSettings.fromJson(budgetSettings)
        val report = BudgetMath.generateDailyBudgetReport(settings, transactions, currentMonth.toString())
        return DashboardSummary(
            currentMonth = currentMonth.toString(),
            income = summary.totals.income,
            expenses = summary.totals.expenses,
            net = summary.totals.net,
            balanceEstimate = settings.balances.netWorth.takeIf { settings.balances.hasAnyBalanceField },
            remainingDailyBudget = report.adjustedDailyTarget,
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
}
