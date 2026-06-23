package com.peterle95.financetracker.domain

import java.time.LocalDate
import java.time.temporal.ChronoUnit
import kotlin.math.abs

enum class ProjectionMode {
    TargetSavings,
    NetWorthTrend,
}

object ProjectionService {
    fun projectionText(
        budgetSettings: BudgetSettings,
        numMonths: Int,
        mode: ProjectionMode = ProjectionMode.TargetSavings,
        historyMonths: Int = 6,
        today: LocalDate = LocalDate.now(),
    ): String = when (mode) {
        ProjectionMode.TargetSavings -> buildTargetSavingsProjection(budgetSettings, numMonths, today)
        ProjectionMode.NetWorthTrend -> buildNetWorthTrendProjection(budgetSettings, numMonths, historyMonths, today)
    }

    private fun buildTargetSavingsProjection(settings: BudgetSettings, numMonths: Int, today: LocalDate): String {
        val bank = settings.balances.bankAccount
        val wallet = settings.balances.wallet
        val savings = settings.balances.savings
        val investments = settings.balances.investments
        val moneyLent = settings.balances.moneyLent
        val dailyGoal = settings.dailySavingsGoal
        val startingTotal = bank + wallet + savings + investments + moneyLent

        return buildString {
            appendLine("=".repeat(80))
            appendLine("FINANCIAL PROJECTION (TARGET SAVINGS)")
            appendLine("=".repeat(80))
            appendLine()
            appendLine("This report projects your total financial balance (Bank + Wallet + Savings + Investments + Money Lent).")
            appendLine("It assumes you will meet your daily savings goal every day.")
            appendLine()
            appendLine("Bank Account Balance:       ${eurPadded(bank, 10)}")
            appendLine("Wallet Balance:             ${eurPadded(wallet, 10)}")
            appendLine("Current Savings Balance:    ${eurPadded(savings, 10)}")
            appendLine("Current Investment Balance: ${eurPadded(investments, 10)}")
            appendLine("Money Lent Balance:         ${eurPadded(moneyLent, 10)}")
            appendLine("-----------------------------------------")
            appendLine("Total Starting Balance:     ${eurPadded(startingTotal, 10)}")
            appendLine("Target Daily Savings Goal:  ${eurPadded(dailyGoal, 10)}")
            appendLine("-".repeat(80))
            appendLine()
            appendLine(formatRow("Month", "Projected Monthly Savings", "Projected Total Balance"))
            appendLine("-".repeat(80))

            var projectedBalance = startingTotal
            var currentDate = today

            repeat(numMonths) {
                val nextMonth = currentDate.plusMonths(1)
                val daysInMonth = ChronoUnit.DAYS.between(currentDate, nextMonth)
                val monthlySavings = dailyGoal * daysInMonth
                projectedBalance += monthlySavings
                appendLine(formatRow(formatMonth(currentDate), eur(monthlySavings), eur(projectedBalance)))
                currentDate = nextMonth
            }

            appendLine("-".repeat(80))
        }
    }

    private fun buildNetWorthTrendProjection(
        settings: BudgetSettings,
        numMonths: Int,
        historyMonths: Int,
        today: LocalDate,
    ): String {
        val snapshots = settings.assetSnapshots

        return buildString {
            appendLine("=".repeat(80))
            appendLine("FINANCIAL PROJECTION (NET WORTH TREND)")
            appendLine("=".repeat(80))
            appendLine()
            appendLine("This report projects your net worth using the average month-by-month change from your snapshot history.")
            appendLine()

            if (snapshots.size < 2) {
                appendLine("Not enough snapshot history to calculate a month-by-month trend.")
                appendLine("Please record at least two net worth snapshots and try again.")
                return@buildString
            }

            val allIntervals = (1 until snapshots.size).map { i ->
                NetWorthInterval(
                    fromDate = snapshots[i - 1].date,
                    toDate = snapshots[i].date,
                    change = snapshots[i].netWorth - snapshots[i - 1].netWorth,
                )
            }

            val monthsRequested = maxOf(1, historyMonths)
            val intervalsUsed = allIntervals.takeLast(monthsRequested)
            val usedChanges = intervalsUsed.map { it.change }
            val avgMonthlyChange = usedChanges.sum() / usedChanges.size
            val latestSnapshot = snapshots.last()

            appendLine("Snapshots available: ${snapshots.size}")
            appendLine("Month-to-month changes available: ${allIntervals.size}")
            appendLine("Months requested for analysis: $monthsRequested")
            appendLine("Months used for analysis: ${intervalsUsed.size}")
            appendLine("Latest snapshot date: ${latestSnapshot.date}")
            appendLine("Latest net worth: ${eur(latestSnapshot.netWorth)}")
            appendLine("-".repeat(80))
            appendLine("AVERAGE CALCULATION DETAILS")
            appendLine(formatRow("Period", "Net Worth Change"))
            appendLine("-".repeat(80))

            for (interval in intervalsUsed) {
                val period = "${interval.fromDate} \u2192 ${interval.toDate}"
                appendLine(formatRow(period, signedEur(interval.change)))
            }

            val changeTerms = usedChanges.joinToString(" + ") { eur(it) }
            appendLine("-".repeat(80))
            appendLine("Average month-by-month change = ($changeTerms) / ${usedChanges.size}")
            appendLine("Average month-by-month change = ${signedEur(avgMonthlyChange)}")
            appendLine("-".repeat(80))
            appendLine()
            appendLine(formatRow("Month", "Projected Net Worth Change", "Projected Net Worth"))
            appendLine("-".repeat(80))

            var projectedNetWorth = latestSnapshot.netWorth
            var currentDate = today

            repeat(numMonths) {
                projectedNetWorth += avgMonthlyChange
                appendLine(
                    formatRow(formatMonth(currentDate), signedEur(avgMonthlyChange), eur(projectedNetWorth)),
                )
                currentDate = currentDate.plusMonths(1)
            }

            appendLine("-".repeat(80))
        }
    }

    private data class NetWorthInterval(
        val fromDate: String,
        val toDate: String,
        val change: Double,
    )

    private fun formatMonth(date: LocalDate): String =
        "%04d-%02d".format(date.year, date.monthValue)

    private fun formatRow(col1: String, col2: String, col3: String = ""): String {
        val padded1 = col1.padEnd(15)
        val padded2 = col2.padEnd(30)
        return if (col3.isEmpty()) "$padded1 $padded2" else "$padded1 $padded2 $col3"
    }

    private fun eur(value: Double): String {
        val sign = if (value < 0) "-" else ""
        return "$sign\u20AC%,.2f".format(abs(value))
    }

    private fun eurPadded(value: Double, width: Int): String {
        val sign = if (value < 0) "-" else ""
        val num = "$sign\u20AC%,.2f".format(abs(value))
        return num.padStart(width + 1)
    }

    private fun signedEur(value: Double): String {
        val sign = if (value >= 0) "+" else "-"
        return "$sign\u20AC%,.2f".format(abs(value))
    }
}
