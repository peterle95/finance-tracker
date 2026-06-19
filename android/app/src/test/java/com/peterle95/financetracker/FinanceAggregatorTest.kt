package com.peterle95.financetracker

import com.peterle95.financetracker.domain.FinanceAggregator
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Test
import java.time.YearMonth

class FinanceAggregatorTest {
    @Test
    fun monthlyAggregationIncludesFixedCostsAndBaseIncome() {
        val budgetSettings = Json.parseToJsonElement(
            """
            {
              "monthly_income": [
                { "amount": 1500, "description": "Base", "start_date": "2026-01-01", "end_date": null }
              ],
              "fixed_costs": [
                { "amount": 500, "desc": "Rent", "start_date": "2026-01-01", "end_date": null }
              ]
            }
            """.trimIndent(),
        ).jsonObject
        val transactions = listOf(
            FinanceTransaction("e1", "e1", TransactionType.Expense, "2026-06-10", 25.0, "Food", "Lunch", null),
            FinanceTransaction("e2", "e2", TransactionType.Expense, "2026-06-11", 75.0, "Food", "Dinner", null),
            FinanceTransaction("i1", "i1", TransactionType.Income, "2026-06-01", 200.0, "Side Gig", "Project", null),
            FinanceTransaction("old", "old", TransactionType.Expense, "2026-05-01", 999.0, "Other", "Old", null),
        )

        val summary = FinanceAggregator.buildInsightsSummary(
            transactions = transactions,
            budgetSettings = budgetSettings,
            endMonth = YearMonth.of(2026, 6),
            monthsBack = 1,
        )

        assertEquals(1700.0, summary.totals.income, 0.0)
        assertEquals(600.0, summary.totals.expenses, 0.0)
        assertEquals(1100.0, summary.totals.net, 0.0)
        assertEquals(100.0, summary.expenseCategories["Food"]!!, 0.0)
        assertEquals(500.0, summary.expenseCategories["Fixed: Rent"]!!, 0.0)
        assertEquals(200.0, summary.incomeCategories["Side Gig"]!!, 0.0)
        assertEquals(1500.0, summary.incomeCategories["Base Monthly Income"]!!, 0.0)
        assertEquals(2, summary.transactionCounts.flexibleExpenses)
        assertEquals(1, summary.transactionCounts.flexibleIncomes)
    }

    @Test
    fun dashboardSummaryUsesProvidedMonth() {
        val budgetSettings = Json.parseToJsonElement(
            """
            {
              "monthly_income": [
                { "amount": 1000, "description": "Base", "start_date": "2026-01-01", "end_date": null }
              ],
              "fixed_costs": []
            }
            """.trimIndent(),
        ).jsonObject
        val transactions = listOf(
            FinanceTransaction("jan", "jan", TransactionType.Expense, "2026-01-10", 10.0, "Food", "January", null),
            FinanceTransaction("feb", "feb", TransactionType.Expense, "2026-02-10", 20.0, "Food", "February", null),
        )

        val january = FinanceAggregator.buildDashboardSummary(
            transactions = transactions,
            budgetSettings = budgetSettings,
            currentMonth = YearMonth.of(2026, 1),
        )
        val february = FinanceAggregator.buildDashboardSummary(
            transactions = transactions,
            budgetSettings = budgetSettings,
            currentMonth = YearMonth.of(2026, 2),
        )

        assertEquals("2026-01", january.currentMonth)
        assertEquals(10.0, january.expenses, 0.0)
        assertEquals("2026-02", february.currentMonth)
        assertEquals(20.0, february.expenses, 0.0)
    }
}
