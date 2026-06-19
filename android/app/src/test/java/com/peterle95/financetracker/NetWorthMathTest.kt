package com.peterle95.financetracker

import com.peterle95.financetracker.domain.AssetBalances
import com.peterle95.financetracker.domain.AssetSnapshot
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.NetWorthMath
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Test
import java.time.LocalDate

class NetWorthMathTest {
    @Test
    fun currentNetWorthSumsAllTrackedBalances() {
        val settings = BudgetSettings(
            balances = AssetBalances(
                bankAccount = 100.0,
                wallet = 20.0,
                savings = 500.0,
                investments = 1000.0,
                moneyLent = -50.0,
            ),
        )

        assertEquals(1570.0, NetWorthMath.currentNetWorth(settings), 0.0)
    }

    @Test
    fun recordAssetSnapshotCreatesAndUpdatesSnapshotForDate() {
        val settings = BudgetSettings(
            balances = AssetBalances(
                bankAccount = 100.0,
                wallet = 20.0,
                savings = 500.0,
                investments = 1000.0,
                moneyLent = 50.0,
            ),
            assetSnapshots = listOf(
                AssetSnapshot(date = "2026-04-01", bankBalance = 50.0, netWorth = 50.0),
            ),
        )

        val added = NetWorthMath.recordAssetSnapshot(settings, "2026-06-18", "Initial")
        val updated = NetWorthMath.recordAssetSnapshot(
            added.copy(balances = settings.balances.copy(bankAccount = 200.0)),
            "2026-06-18",
            "Updated",
        )

        assertEquals(listOf("2026-04-01", "2026-06-18"), updated.assetSnapshots.map { it.date })
        assertEquals(1770.0, updated.assetSnapshots.last().netWorth, 0.0)
        assertEquals("Updated", updated.assetSnapshots.last().note)
    }

    @Test
    fun netWorthChangeUsesClosestSnapshotBeforeTargetDate() {
        val settings = BudgetSettings(
            balances = AssetBalances(bankAccount = 2000.0),
            assetSnapshots = listOf(
                AssetSnapshot(date = "2026-01-01", bankBalance = 1000.0, netWorth = 1000.0),
                AssetSnapshot(date = "2026-03-15", bankBalance = 1500.0, netWorth = 1500.0),
            ),
        )

        val change = NetWorthMath.netWorthChange(settings, 3, LocalDate.of(2026, 6, 18))

        assertNotNull(change)
        assertEquals("2026-03-15", change!!.pastDate)
        assertEquals(500.0, change.change, 0.0)
        assertEquals(33.333, change.changePercent, 0.001)
    }
}
