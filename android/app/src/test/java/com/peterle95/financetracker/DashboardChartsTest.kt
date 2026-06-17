package com.peterle95.financetracker

import com.peterle95.financetracker.domain.BarBreakdownMode
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.ChartDisplayMode
import com.peterle95.financetracker.domain.DashboardCharts
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.ReportDateMode
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate
import java.time.YearMonth

class DashboardChartsTest {
    @Test
    fun pieChartUsesBehaviorDateInBnplModeAndBookedDateInNormalMode() {
        val bnplPie = DashboardCharts.buildPieChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            month = "2026-06",
            type = TransactionType.Expense,
            includeFixedCosts = false,
            includeBaseIncome = false,
            showBudgetStatus = false,
            sortByValue = true,
            dateMode = ReportDateMode.BNPL,
        )
        val normalPie = DashboardCharts.buildPieChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            month = "2026-06",
            type = TransactionType.Expense,
            includeFixedCosts = false,
            includeBaseIncome = false,
            showBudgetStatus = false,
            sortByValue = true,
            dateMode = ReportDateMode.Normal,
        )

        assertEquals(75.0, bnplPie.entries.first { it.label == "Shopping" }.value, 0.0)
        assertTrue(normalPie.entries.none { it.label == "Shopping" })
    }

    @Test
    fun pieChartMatchesDesktopTotalsWithFixedCostsAndBaseIncome() {
        val expensePie = DashboardCharts.buildPieChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            month = "2026-06",
            type = TransactionType.Expense,
            includeFixedCosts = true,
            includeBaseIncome = false,
            showBudgetStatus = true,
            sortByValue = false,
            dateMode = ReportDateMode.BNPL,
        )
        val incomePie = DashboardCharts.buildPieChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            month = "2026-06",
            type = TransactionType.Income,
            includeFixedCosts = false,
            includeBaseIncome = true,
            showBudgetStatus = false,
            sortByValue = false,
            dateMode = ReportDateMode.BNPL,
        )

        assertEquals(500.0, expensePie.entries.first { it.label == "Fixed Costs" }.value, 0.0)
        assertEquals(65.0, expensePie.entries.first { it.label == "Food" }.value, 0.0)
        assertTrue(expensePie.budgetInfo.any { it.startsWith("Food:") })
        assertEquals(1500.0, incomePie.entries.first { it.label == "Base Income" }.value, 0.0)
        assertEquals(200.0, incomePie.entries.first { it.label == "Side Gig" }.value, 0.0)
    }

    @Test
    fun historicalBarCoversRequestedMonthsAndOptionalBaseValues() {
        val chart = DashboardCharts.buildHistoricalBarChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            categories = categories,
            numMonths = 2,
            endMonth = YearMonth.of(2026, 7),
            type = TransactionType.Expense,
            includeFixedCosts = true,
            includeBaseIncome = false,
            breakdownMode = BarBreakdownMode.Total,
            displayMode = ChartDisplayMode.Value,
            dateMode = ReportDateMode.BNPL,
        )

        assertEquals(listOf("2026-06", "2026-07"), chart.labels)
        assertEquals(listOf(640.0, 560.0), chart.series.single().values)
    }

    @Test
    fun historicalBarSupportsCategoryFlexibleAndOverUnderBreakdowns() {
        val categoryChart = DashboardCharts.buildHistoricalBarChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            categories = categories,
            numMonths = 2,
            endMonth = YearMonth.of(2026, 7),
            type = TransactionType.Expense,
            includeFixedCosts = true,
            includeBaseIncome = false,
            breakdownMode = BarBreakdownMode.Categories,
            displayMode = ChartDisplayMode.Value,
            dateMode = ReportDateMode.BNPL,
        )
        val flexibleChart = DashboardCharts.buildHistoricalBarChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            categories = categories,
            numMonths = 2,
            endMonth = YearMonth.of(2026, 7),
            type = TransactionType.Expense,
            includeFixedCosts = false,
            includeBaseIncome = false,
            breakdownMode = BarBreakdownMode.Flexible,
            displayMode = ChartDisplayMode.Value,
            dateMode = ReportDateMode.BNPL,
        )
        val overUnderChart = DashboardCharts.buildHistoricalBarChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            categories = categories,
            numMonths = 2,
            endMonth = YearMonth.of(2026, 7),
            type = TransactionType.Expense,
            includeFixedCosts = false,
            includeBaseIncome = false,
            breakdownMode = BarBreakdownMode.OverUnder,
            displayMode = ChartDisplayMode.Percentage,
            dateMode = ReportDateMode.BNPL,
        )

        assertTrue(categoryChart.series.any { it.label == "Fixed Costs" })
        assertEquals(listOf("Flexible Income", "Flexible Costs"), flexibleChart.series.map { it.label })
        assertEquals(listOf("Net Result"), overUnderChart.series.map { it.label })
    }

    @Test
    fun dayOfWeekAverageUsesUniqueSpendingDays() {
        val chart = DashboardCharts.buildDayOfWeekChart(
            transactions = transactions,
            monthsBack = 1,
            today = LocalDate.of(2026, 6, 30),
            dateMode = ReportDateMode.BNPL,
        )
        val mondayIndex = chart.labels.indexOf("Mon")

        assertEquals(2, chart.counts[mondayIndex])
        assertEquals(57.5, chart.averages[mondayIndex], 0.0)
    }

    @Test
    fun spendingPaceCalculatesCumulativeSpendingAndBudgetPace() {
        val chart = DashboardCharts.buildSpendingPaceChart(
            transactions = transactions,
            budgetSettings = budgetSettings,
            month = "2026-06",
            today = LocalDate.of(2026, 6, 2),
            dateMode = ReportDateMode.BNPL,
        )

        assertEquals(listOf(1, 2), chart.days)
        assertEquals(700.0, chart.monthlyBudget, 0.0)
        assertEquals(listOf(40.0, 65.0), chart.cumulativeSpending)
        assertEquals(700.0 / 30.0, chart.budgetPace[0], 0.0001)
        assertEquals(700.0 * 2.0 / 30.0, chart.budgetPace[1], 0.0001)
    }

    private val categories = CategoryState(
        expenses = listOf("Food", "Shopping", "Travel"),
        incomes = listOf("Side Gig", "Gift"),
    )

    private val transactions = listOf(
        FinanceTransaction("food-1", "food-1", TransactionType.Expense, "2026-06-01", 40.0, "Food", "Groceries", null),
        FinanceTransaction("food-2", "food-2", TransactionType.Expense, "2026-06-02", 25.0, "Food", "Lunch", null),
        FinanceTransaction("bnpl", "bnpl", TransactionType.Expense, "2026-07-01", 75.0, "Shopping", "BNPL shoes", "2026-06-22"),
        FinanceTransaction("travel", "travel", TransactionType.Expense, "2026-07-03", 60.0, "Travel", "Train", null),
        FinanceTransaction("side", "side", TransactionType.Income, "2026-06-05", 200.0, "Side Gig", "Project", null),
    )

    private val budgetSettings = Json.parseToJsonElement(
        """
        {
          "monthly_income": [
            { "amount": 1500, "description": "Base", "start_date": "2026-01-01", "end_date": null }
          ],
          "fixed_costs": [
            { "amount": 500, "desc": "Rent", "start_date": "2026-01-01", "end_date": null }
          ],
          "daily_savings_goal": 10,
          "category_budgets": {
            "Expense": {
              "Food": 40,
              "Shopping": 20
            }
          }
        }
        """.trimIndent(),
    ).jsonObject
}
