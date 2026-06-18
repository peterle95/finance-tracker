package com.peterle95.financetracker

import com.peterle95.financetracker.domain.BudgetMath
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class BudgetMathTest {
    @Test
    fun activeFixedCostsUseStartAndEndDateOverlap() {
        val settings = budgetSettings(
            """
            {
              "fixed_costs": [
                { "amount": 100, "desc": "Old", "start_date": "2026-01-01", "end_date": "2026-05-31" },
                { "amount": 200, "desc": "Current", "start_date": "2026-06-15", "end_date": null },
                { "amount": 300, "desc": "Future", "start_date": "2026-07-01", "end_date": null }
              ]
            }
            """.trimIndent(),
        )

        val active = BudgetMath.activeFixedCosts(settings, "2026-06")

        assertEquals(listOf("Current"), active.map { it.description })
        assertEquals(200.0, active.single().amount, 0.0)
    }

    @Test
    fun activeMonthlyIncomeSupportsDateRangesAndLegacyNumber() {
        val ranged = budgetSettings(
            """
            {
              "monthly_income": [
                { "amount": 1000, "description": "Old", "start_date": "2026-01-01", "end_date": "2026-05-31" },
                { "amount": 1500, "description": "Current", "start_date": "2026-06-01", "end_date": null }
              ]
            }
            """.trimIndent(),
        )
        val legacy = budgetSettings("""{ "monthly_income": 2200 }""")

        assertEquals(1500.0, BudgetMath.activeMonthlyIncome(ranged, "2026-06"), 0.0)
        assertEquals(2200.0, BudgetMath.activeMonthlyIncome(legacy, "2026-06"), 0.0)
    }

    @Test
    fun dailyBudgetReportUsesDesktopFlexibleBudgetMath() {
        val settings = budgetSettings(
            """
            {
              "monthly_income": [
                { "amount": 3000, "description": "Salary", "start_date": "2026-01-01", "end_date": null }
              ],
              "fixed_costs": [
                { "amount": 1000, "desc": "Rent", "start_date": "2026-01-01", "end_date": null }
              ],
              "daily_savings_goal": 10
            }
            """.trimIndent(),
        )
        val rows = listOf(
            FinanceTransaction("e1", "e1", TransactionType.Expense, "2026-06-01", 50.0, "Food", "Groceries", null),
            FinanceTransaction("i1", "i1", TransactionType.Income, "2026-06-02", 200.0, "Bonus", "Bonus", null),
            FinanceTransaction("e2", "e2", TransactionType.Expense, "2026-06-02", 100.0, "Food", "Dinner", null),
        )

        val report = BudgetMath.generateDailyBudgetReport(
            settings = settings,
            transactions = rows,
            month = "2026-06",
            today = LocalDate.of(2026, 6, 2),
        )

        assertEquals(1700.0, report.netMonthlyFlexibleBudget, 0.0)
        assertEquals(56.666, report.initialDailySpendingTarget, 0.001)
        assertEquals(2, report.days.size)
        assertEquals(1650.0, report.days[0].cumulativeFlexibleBalance, 0.0)
        assertEquals(1750.0, report.days[1].cumulativeFlexibleBalance, 0.0)
        assertEquals(1750.0 / 29.0, report.adjustedDailyTarget, 0.001)
        assertTrue(report.textReport.contains("DAILY BUDGET REPORT"))
    }

    @Test
    fun negativeCarryoverIncludesOnlyPreviousMonthDeficit() {
        val settings = budgetSettings(
            """
            {
              "monthly_income": [
                { "amount": 1000, "description": "Salary", "start_date": "2026-01-01", "end_date": null }
              ],
              "fixed_costs": [],
              "daily_savings_goal": 0
            }
            """.trimIndent(),
        )
        val rows = listOf(
            FinanceTransaction("may", "may", TransactionType.Expense, "2026-05-10", 1200.0, "Food", "May", null),
        )

        val carryover = BudgetMath.negativeCarryoverFromPreviousMonth(settings, rows, "2026-06")
        val report = BudgetMath.generateDailyBudgetReport(
            settings = settings,
            transactions = rows,
            month = "2026-06",
            includeNegativeCarryover = true,
            today = LocalDate.of(2026, 6, 1),
        )

        assertEquals(-200.0, carryover, 0.0)
        assertEquals(800.0, report.netMonthlyFlexibleBudget, 0.0)
    }

    private fun budgetSettings(content: String): BudgetSettings =
        BudgetSettings.fromJson(Json.parseToJsonElement(content).jsonObject)
}
