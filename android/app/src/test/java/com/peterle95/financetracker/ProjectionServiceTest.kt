package com.peterle95.financetracker

import com.peterle95.financetracker.domain.AssetBalances
import com.peterle95.financetracker.domain.AssetSnapshot
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.ProjectionMode
import com.peterle95.financetracker.domain.ProjectionService
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.time.LocalDate

class ProjectionServiceTest {
    @Test
    fun targetSavingsUsesBalancesAndDailyGoal() {
        val settings = BudgetSettings(
            balances = AssetBalances(
                bankAccount = 500.0,
                wallet = 200.0,
                savings = 100.0,
                investments = 100.0,
                moneyLent = 100.0,
            ),
            dailySavingsGoal = 10.0,
        )

        val today = LocalDate.of(2025, 1, 1)
        val result = ProjectionService.projectionText(settings, 3, ProjectionMode.TargetSavings, today = today)

        assertTrue(result.contains("FINANCIAL PROJECTION (TARGET SAVINGS)"))
        assertTrue(result.contains("Total Starting Balance:"))
        assertTrue(result.contains("1,000.00"))
        assertTrue(result.contains("Target Daily Savings Goal:"))
        assertTrue(result.contains("10.00"))
        assertTrue(result.contains("2025-01"))
        assertTrue(result.contains("2025-02"))
        assertTrue(result.contains("2025-03"))
    }

    @Test
    fun netWorthTrendReturnsNotEnoughHistoryWithFewerThanTwoSnapshots() {
        val settings = BudgetSettings(
            assetSnapshots = listOf(
                AssetSnapshot(date = "2025-01-01", bankBalance = 1000.0, netWorth = 1000.0),
            ),
        )

        val result = ProjectionService.projectionText(
            settings, 12, ProjectionMode.NetWorthTrend, today = LocalDate.of(2025, 6, 1),
        )

        assertTrue(result.contains("Not enough snapshot history"))
    }

    @Test
    fun netWorthTrendCalculatesAverageMonthlyChangeCorrectly() {
        val settings = BudgetSettings(
            assetSnapshots = listOf(
                AssetSnapshot(date = "2025-01-01", bankBalance = 1000.0, netWorth = 1000.0),
                AssetSnapshot(date = "2025-02-01", bankBalance = 1100.0, netWorth = 1100.0),
                AssetSnapshot(date = "2025-03-01", bankBalance = 1200.0, netWorth = 1200.0),
            ),
        )

        val today = LocalDate.of(2025, 6, 1)
        val result = ProjectionService.projectionText(
            settings, 2, ProjectionMode.NetWorthTrend, historyMonths = 6, today = today,
        )

        assertTrue(result.contains("Snapshots available: 3"))
        assertTrue(result.contains("Latest net worth:"))
        assertTrue(result.contains("1,200.00"))

        // avg change = (100 + 100) / 2 = 100
        // starting from 1200: month 1 = 1300, month 2 = 1400
        assertTrue(result.contains("2025-06"))
        assertTrue(result.contains("2025-07"))
        assertTrue(result.contains("+€100.00"))
        assertTrue(result.contains("1,400.00"))
    }
}
