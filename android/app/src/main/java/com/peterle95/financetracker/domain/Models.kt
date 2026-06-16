package com.peterle95.financetracker.domain

import java.time.LocalDate

enum class TransactionType(val label: String) {
    Expense("Expense"),
    Income("Income");

    companion object {
        fun fromLabel(value: String): TransactionType =
            entries.firstOrNull { it.label.equals(value, ignoreCase = true) } ?: Expense
    }
}

data class FinanceTransaction(
    val localId: Long,
    val exportId: String?,
    val type: TransactionType,
    val date: String,
    val amount: Double,
    val category: String,
    val description: String,
    val behaviorDate: String?,
)

data class CategoryState(
    val expenses: List<String> = CategoryDefaults.expense,
    val incomes: List<String> = CategoryDefaults.income,
) {
    fun forType(type: TransactionType): List<String> =
        if (type == TransactionType.Expense) expenses else incomes
}

data class FinanceTotals(
    val income: Double,
    val expenses: Double,
    val net: Double,
    val fixedCosts: Double,
    val baseIncome: Double,
    val flexibleExpenses: Double,
    val flexibleIncome: Double,
)

data class TransactionCounts(
    val flexibleExpenses: Int,
    val flexibleIncomes: Int,
)

data class InsightsSummary(
    val months: List<String>,
    val totals: FinanceTotals,
    val expenseCategories: Map<String, Double>,
    val incomeCategories: Map<String, Double>,
    val transactionCounts: TransactionCounts,
)

data class DashboardSummary(
    val currentMonth: String,
    val income: Double,
    val expenses: Double,
    val net: Double,
    val topExpenseCategories: List<Pair<String, Double>>,
    val balanceEstimate: Double?,
)

fun todayIsoDate(): String = LocalDate.now().toString()
