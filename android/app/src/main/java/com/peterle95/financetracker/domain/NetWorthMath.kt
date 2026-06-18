package com.peterle95.financetracker.domain

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

object NetWorthMath {
    private val periods = listOf(1, 3, 6, 12)

    fun currentNetWorth(settings: BudgetSettings): Double =
        settings.balances.netWorth

    fun createSnapshot(settings: BudgetSettings, date: String, note: String = ""): AssetSnapshot =
        AssetSnapshot(
            date = date,
            bankBalance = settings.balances.bankAccount,
            walletBalance = settings.balances.wallet,
            savingsBalance = settings.balances.savings,
            investmentBalance = settings.balances.investments,
            moneyLentBalance = settings.balances.moneyLent,
            note = note,
            netWorth = currentNetWorth(settings),
        )

    fun recordAssetSnapshot(settings: BudgetSettings, date: String, note: String = ""): BudgetSettings {
        val snapshot = createSnapshot(settings, date, note)
        val snapshots = (settings.assetSnapshots.filterNot { it.date == date } + snapshot)
            .sortedBy { it.date }
        return settings.copy(assetSnapshots = snapshots)
    }

    fun deleteSnapshot(settings: BudgetSettings, date: String): BudgetSettings =
        settings.copy(assetSnapshots = settings.assetSnapshots.filterNot { it.date == date })

    fun netWorthChange(
        settings: BudgetSettings,
        periodMonths: Int,
        today: LocalDate = LocalDate.now(),
    ): NetWorthChange? {
        if (settings.assetSnapshots.isEmpty()) return null
        val targetDate = today.minusMonths(periodMonths.toLong())
        val pastSnapshot = settings.assetSnapshots
            .filter { it.date.parseDateOrNull()?.let { date -> !date.isAfter(targetDate) } == true }
            .maxByOrNull { it.date }
            ?: return null
        val current = currentNetWorth(settings)
        val change = current - pastSnapshot.netWorth
        val percent = if (pastSnapshot.netWorth != 0.0) {
            change / pastSnapshot.netWorth * 100.0
        } else {
            0.0
        }
        return NetWorthChange(
            months = periodMonths,
            current = current,
            past = pastSnapshot.netWorth,
            change = change,
            changePercent = percent,
            pastDate = pastSnapshot.date,
        )
    }

    fun assetAllocation(settings: BudgetSettings): List<AssetAllocation> {
        val assets = listOf(
            "Bank Account" to settings.balances.bankAccount,
            "Wallet" to settings.balances.wallet,
            "Savings" to settings.balances.savings,
            "Investments" to settings.balances.investments,
            "Money Lent" to settings.balances.moneyLent,
        )
        val positiveTotal = assets.filter { it.second > 0.0 }.sumOf { it.second }
        if (positiveTotal <= 0.0) return emptyList()
        return assets
            .filter { it.second > 0.0 }
            .map { (label, value) ->
                AssetAllocation(
                    label = label,
                    value = value,
                    percent = value / positiveTotal * 100.0,
                )
            }
    }

    fun buildSummary(settings: BudgetSettings, today: LocalDate = LocalDate.now()): NetWorthSummary =
        NetWorthSummary(
            currentNetWorth = currentNetWorth(settings),
            balances = settings.balances,
            changes = periods.associateWith { netWorthChange(settings, it, today) },
            snapshots = settings.assetSnapshots,
            allocation = assetAllocation(settings),
            reportText = generateNetWorthReport(settings, today),
        )

    fun generateNetWorthReport(settings: BudgetSettings, today: LocalDate = LocalDate.now()): String {
        val snapshots = settings.assetSnapshots
        val current = currentNetWorth(settings)
        val generatedDate = today.format(DateTimeFormatter.ofPattern("MMMM dd, yyyy", Locale.US))

        return buildString {
            appendLine("=".repeat(80))
            appendLine("NET WORTH REPORT")
            appendLine("=".repeat(80))
            appendLine()
            appendLine("Generated: $generatedDate")
            appendLine()
            appendLine("CURRENT ASSET BREAKDOWN")
            appendLine("-".repeat(80))
            appendLine("Bank Account:        ${eur(settings.balances.bankAccount, 12)}")
            appendLine("Wallet:              ${eur(settings.balances.wallet, 12)}")
            appendLine("Savings:             ${eur(settings.balances.savings, 12)}")
            appendLine("Investments:         ${eur(settings.balances.investments, 12)}")
            appendLine("Money Lent:          ${eur(settings.balances.moneyLent, 12)}")
            appendLine("-".repeat(80))
            appendLine("CURRENT NET WORTH:   ${eur(current, 12)}")
            appendLine()

            if (snapshots.isEmpty()) {
                appendLine("No historical snapshots recorded yet.")
                appendLine("Start tracking by recording your first snapshot!")
                return@buildString
            }

            appendLine("=".repeat(80))
            appendLine("HISTORICAL CHANGES")
            appendLine("=".repeat(80))
            appendLine()
            periods.forEach { months ->
                netWorthChange(settings, months, today)?.let { change ->
                    val sign = if (change.change >= 0.0) "+" else ""
                    appendLine("Change over $months month(s) (since ${change.pastDate}):")
                    appendLine("  $sign${eur(change.change)} ($sign${"%.1f".format(change.changePercent)}%)")
                    appendLine("  From: ${eur(change.past)} -> To: ${eur(change.current)}")
                    appendLine()
                }
            }

            appendLine()
            appendLine("=".repeat(80))
            appendLine("SNAPSHOT HISTORY")
            appendLine("=".repeat(80))
            appendLine()
            appendLine("${"Date".padEnd(12)} ${"Net Worth".padStart(15)} ${"Change".padStart(15)} Note")
            appendLine("-".repeat(80))

            snapshots.forEachIndexed { index, snapshot ->
                val changeText = if (index > 0) {
                    val change = snapshot.netWorth - snapshots[index - 1].netWorth
                    val sign = if (change >= 0.0) "+" else ""
                    "$sign${eur(change)}"
                } else {
                    "-"
                }
                appendLine(
                    snapshot.date.padEnd(12) + " " +
                        eur(snapshot.netWorth, 13).padStart(15) + " " +
                        changeText.padStart(15) + " " +
                        snapshot.note.take(30),
                )
            }

            val latest = snapshots.last()
            appendLine()
            appendLine("-".repeat(80))
            appendLine("Latest snapshot from: ${latest.date}")
            appendLine("Latest recorded net worth: ${eur(latest.netWorth)}")
            if (latest.date != today.toString()) {
                val diff = current - latest.netWorth
                val sign = if (diff >= 0.0) "+" else ""
                appendLine("Change since last snapshot: $sign${eur(diff)}")
            }
        }
    }

    private fun String.parseDateOrNull(): LocalDate? =
        runCatching { LocalDate.parse(this) }.getOrNull()

    private fun eur(value: Double, width: Int? = null): String {
        val text = "\u20AC%,.2f".format(value)
        return if (width == null) text else text.padStart(width + 1)
    }
}
