package com.peterle95.financetracker.domain

import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeParseException
import java.util.Locale

object BudgetMath {
    fun activeFixedCosts(settings: BudgetSettings, month: String): List<FixedCost> {
        val yearMonth = parseMonth(month) ?: return settings.fixedCosts
        return settings.fixedCosts.filter { it.isActiveForMonth(yearMonth) }
    }

    fun activeMonthlyIncomeSources(settings: BudgetSettings, month: String): List<IncomeSource> {
        val yearMonth = parseMonth(month) ?: return emptyList()
        return settings.monthlyIncome.filter { it.isActiveForMonth(yearMonth) }
    }

    fun activeMonthlyIncome(settings: BudgetSettings, month: String): Double =
        activeMonthlyIncomeSources(settings, month).sumOf { it.amount }

    fun daysInMonth(month: String): Int =
        parseMonth(month)?.lengthOfMonth() ?: 30

    fun previousMonth(month: String): String? =
        parseMonth(month)?.minusMonths(1)?.toString()

    fun monthEndFlexibleBalance(
        settings: BudgetSettings,
        transactions: List<FinanceTransaction>,
        month: String,
    ): Double {
        val yearMonth = parseMonth(month) ?: return 0.0
        val baseIncome = activeMonthlyIncome(settings, month)
        val fixedCosts = activeFixedCosts(settings, month).sumOf { it.amount }
        val monthlySavingsGoal = settings.dailySavingsGoal * yearMonth.lengthOfMonth()
        val monthlyFlexibleBudget = baseIncome - fixedCosts - monthlySavingsGoal
        val flexibleIncome = transactions
            .filter { it.type == TransactionType.Income && it.date.take(7) == month }
            .sumOf { it.amount }
        val flexibleExpenses = transactions
            .filter { it.type == TransactionType.Expense && it.date.take(7) == month }
            .sumOf { it.amount }

        return monthlyFlexibleBudget + flexibleIncome - flexibleExpenses
    }

    fun negativeCarryoverFromPreviousMonth(
        settings: BudgetSettings,
        transactions: List<FinanceTransaction>,
        month: String,
    ): Double {
        val previousMonth = previousMonth(month) ?: return 0.0
        val previousBalance = monthEndFlexibleBalance(settings, transactions, previousMonth)
        return if (previousBalance < 0.0) previousBalance else 0.0
    }

    fun computeNetAvailableForSpending(
        settings: BudgetSettings,
        transactions: List<FinanceTransaction>,
        month: String,
        dateMode: ReportDateMode = ReportDateMode.Normal,
    ): Double {
        val normalizedMonth = parseMonth(month)?.toString() ?: YearMonth.now().toString()
        val baseIncome = activeMonthlyIncome(settings, normalizedMonth)
        val flexibleIncome = transactions
            .filter { it.type == TransactionType.Income && it.reportMonth(dateMode) == normalizedMonth }
            .sumOf { it.amount }
        val fixedCosts = activeFixedCosts(settings, normalizedMonth).sumOf { it.amount }
        val monthlySavingsGoal = settings.dailySavingsGoal * daysInMonth(normalizedMonth)
        return maxOf(baseIncome + flexibleIncome - fixedCosts - monthlySavingsGoal, 0.0)
    }

    fun generateDailyBudgetReport(
        settings: BudgetSettings,
        transactions: List<FinanceTransaction>,
        month: String,
        includeNegativeCarryover: Boolean = false,
        today: LocalDate = LocalDate.now(),
    ): BudgetReport {
        val yearMonth = parseMonth(month)
            ?: return BudgetReport.invalid(month, "Invalid month format. Use YYYY-MM.")
        val monthText = yearMonth.toString()
        val daysInMonth = yearMonth.lengthOfMonth()
        val baseIncome = activeMonthlyIncome(settings, monthText)
        val fixedCosts = activeFixedCosts(settings, monthText).sumOf { it.amount }
        val monthlySavingsGoal = settings.dailySavingsGoal * daysInMonth
        val flexibleIncome = transactions
            .filter { it.type == TransactionType.Income && it.date.take(7) == monthText }
            .sumOf { it.amount }
        val totalIncome = baseIncome + flexibleIncome
        val carryover = if (includeNegativeCarryover) {
            negativeCarryoverFromPreviousMonth(settings, transactions, monthText)
        } else {
            0.0
        }
        val netMonthlyFlexibleBudget = baseIncome - fixedCosts - monthlySavingsGoal + carryover
        val initialDailyTarget = if (daysInMonth > 0) netMonthlyFlexibleBudget / daysInMonth else 0.0
        val dailyIncome = transactions
            .filter { it.type == TransactionType.Income && it.date.take(7) == monthText }
            .groupBy { it.date }
            .mapValues { (_, rows) -> rows.sumOf { it.amount } }
        val dailyExpenses = transactions
            .filter { it.type == TransactionType.Expense && it.date.take(7) == monthText }
            .groupBy { it.date }
            .mapValues { (_, rows) -> rows.sumOf { it.amount } }

        val rows = mutableListOf<BudgetReportDay>()
        var cumulativeFlexibleBalance = netMonthlyFlexibleBudget
        for (day in 1..daysInMonth) {
            val date = yearMonth.atDay(day)
            if (date > today) break

            val dateText = date.toString()
            cumulativeFlexibleBalance += dailyIncome[dateText] ?: 0.0
            val remainingDaysIncludingToday = daysInMonth - day + 1
            val dailyTarget = if (cumulativeFlexibleBalance <= 0.0) {
                0.0
            } else {
                cumulativeFlexibleBalance / remainingDaysIncludingToday
            }
            val spent = dailyExpenses[dateText] ?: 0.0
            cumulativeFlexibleBalance -= spent
            val delta = dailyTarget - spent
            val status = when {
                spent == 0.0 -> "No spending"
                delta >= 0.0 -> "On Track"
                else -> "Overspent"
            }

            rows += BudgetReportDay(
                date = dateText,
                target = dailyTarget,
                spent = spent,
                dailyDelta = delta,
                cumulativeFlexibleBalance = cumulativeFlexibleBalance,
                status = status,
            )
        }

        val remainingDays = remainingDays(yearMonth, today)
        val adjustedDailyTarget = if (remainingDays > 0 && cumulativeFlexibleBalance > 0.0) {
            cumulativeFlexibleBalance / remainingDays
        } else {
            0.0
        }
        val status = statusFor(
            cumulativeFlexibleBalance = cumulativeFlexibleBalance,
            adjustedDailyTarget = adjustedDailyTarget,
            initialDailyTarget = initialDailyTarget,
            remainingDays = remainingDays,
        )
        val monthLabel = yearMonth.month.getDisplayName(java.time.format.TextStyle.FULL, Locale.US) +
            " ${yearMonth.year}"

        val reportWithoutText = BudgetReport(
            month = monthText,
            monthLabel = monthLabel,
            baseMonthlyIncome = baseIncome,
            fixedCosts = fixedCosts,
            dailySavingsGoal = settings.dailySavingsGoal,
            monthlySavingsGoal = monthlySavingsGoal,
            netMonthlyFlexibleBudget = netMonthlyFlexibleBudget,
            initialDailySpendingTarget = initialDailyTarget,
            flexibleIncomeThisMonth = flexibleIncome,
            totalIncome = totalIncome,
            carryoverAmount = carryover,
            includeNegativeCarryover = includeNegativeCarryover,
            remainingFlexibleBudget = cumulativeFlexibleBalance,
            remainingDays = remainingDays,
            adjustedDailyTarget = adjustedDailyTarget,
            days = rows,
            statusTitle = status.first,
            statusDetail = status.second,
            textReport = "",
        )

        return reportWithoutText.copy(textReport = buildTextReport(reportWithoutText, yearMonth, today))
    }

    private fun buildTextReport(report: BudgetReport, yearMonth: YearMonth, today: LocalDate): String {
        val previousMonthLabel = previousMonth(report.month) ?: "N/A"
        return buildString {
            appendLine("=".repeat(80))
            appendLine("DAILY BUDGET REPORT - ${report.monthLabel}")
            appendLine("=".repeat(80))
            appendLine()
            appendLine("Base Monthly Income:                      ${eur(report.baseMonthlyIncome, 10)}")
            appendLine("Total Fixed Costs:                       -${eur(report.fixedCosts, 10)}")
            appendLine("-".repeat(50))
            appendLine("Monthly Savings Goal:                    -${eur(report.monthlySavingsGoal, 10)}")
            if (report.includeNegativeCarryover) {
                appendLine("Negative Carryover ($previousMonthLabel):             ${eur(report.carryoverAmount, 10)}")
            }
            appendLine("NET MONTHLY FLEXIBLE BUDGET:              ${eur(report.netMonthlyFlexibleBudget, 10)}")
            appendLine("INITIAL DAILY SPENDING TARGET:            ${eur(report.initialDailySpendingTarget, 10)}")
            appendLine("-".repeat(50))
            appendLine()
            appendLine("Flexible Income (This Month):             ${eur(report.flexibleIncomeThisMonth, 10)}")
            appendLine("TOTAL INCOME:                             ${eur(report.totalIncome, 10)}")
            appendLine("-".repeat(80))
            appendLine()
            appendLine("DAILY BREAKDOWN (Flexible daily target adjusts based on remaining budget)")
            appendLine("-".repeat(80))
            appendLine("${"Date".padEnd(12)} ${"Target".padEnd(12)} ${"Spent".padEnd(12)} ${"Daily +/-".padEnd(12)} ${"Cumulative".padEnd(12)} Status")
            appendLine("-".repeat(80))

            report.days.forEach { day ->
                appendLine(
                    day.date.padEnd(12) + " " +
                        eur(day.target).padEnd(12) + " " +
                        eur(day.spent).padEnd(12) + " " +
                        eur(day.dailyDelta).padEnd(12) + " " +
                        eur(day.cumulativeFlexibleBalance).padEnd(12) + " " +
                        day.status,
                )
            }
            appendLine("-".repeat(80))
            appendLine()

            if (today.year == yearMonth.year && today.month == yearMonth.month && today.dayOfMonth < yearMonth.lengthOfMonth()) {
                appendLine("=".repeat(80))
                appendLine("YOUR PATH FORWARD")
                appendLine("=".repeat(80))
                appendLine()
                appendLine(report.statusTitle.uppercase())
                appendLine()
                appendLine(report.statusDetail)
                appendLine()
                appendLine("Days remaining: ${report.remainingDays}")
                appendLine("Remaining flexible budget: ${eur(report.remainingFlexibleBudget)}")
                appendLine("Adjusted daily target: ${eur(report.adjustedDailyTarget)}")
                appendLine()
            } else if (today.year == yearMonth.year && today.month == yearMonth.month) {
                val endText = if (report.remainingFlexibleBudget < 0.0) {
                    "Month Complete: You overspent your flexible budget by ${eur(kotlin.math.abs(report.remainingFlexibleBudget))}"
                } else {
                    "Month Complete: You have ${eur(report.remainingFlexibleBudget)} remaining in your flexible budget."
                }
                appendLine(endText)
            }
        }
    }

    private fun statusFor(
        cumulativeFlexibleBalance: Double,
        adjustedDailyTarget: Double,
        initialDailyTarget: Double,
        remainingDays: Int,
    ): Pair<String, String> =
        when {
            remainingDays <= 0 -> {
                if (cumulativeFlexibleBalance < 0.0) {
                    "Month complete" to "The month ended over the flexible budget."
                } else {
                    "Month complete" to "The month ended with flexible budget remaining."
                }
            }

            cumulativeFlexibleBalance <= 0.0 -> {
                "Budget depleted" to "Spend EUR0.00 per day for the remaining days to avoid increasing the deficit."
            }

            adjustedDailyTarget <= initialDailyTarget * 0.7 -> {
                "Spending caution needed" to "Try to limit spending to the adjusted daily target for the rest of the month."
            }

            adjustedDailyTarget >= initialDailyTarget * 1.3 -> {
                "Excellent progress" to "Spending is below pace, so the remaining daily target has increased."
            }

            else -> {
                "On track" to "Spending is close to plan for the selected month."
            }
        }

    private fun remainingDays(yearMonth: YearMonth, today: LocalDate): Int =
        when {
            today < yearMonth.atDay(1) -> yearMonth.lengthOfMonth()
            today > yearMonth.atEndOfMonth() -> 0
            else -> yearMonth.lengthOfMonth() - today.dayOfMonth + 1
        }

    private fun IncomeSource.isActiveForMonth(yearMonth: YearMonth): Boolean =
        activeForMonth(startDate, endDate, yearMonth)

    private fun FixedCost.isActiveForMonth(yearMonth: YearMonth): Boolean =
        activeForMonth(startDate, endDate, yearMonth)

    private fun activeForMonth(startDate: String, endDate: String?, yearMonth: YearMonth): Boolean {
        val monthStart = yearMonth.atDay(1)
        val monthEnd = yearMonth.atEndOfMonth()
        val start = startDate.parseIsoDateOrNull() ?: LocalDate.of(2000, 1, 1)
        val end = endDate?.parseIsoDateOrNull()
        return !start.isAfter(monthEnd) && (end == null || !end.isBefore(monthStart))
    }

    private fun parseMonth(month: String): YearMonth? =
        try {
            YearMonth.parse(month)
        } catch (_: DateTimeParseException) {
            null
        }

    private fun FinanceTransaction.reportDate(mode: ReportDateMode): String =
        if (mode == ReportDateMode.BNPL) behaviorDate?.takeIf { it.isNotBlank() } ?: date else date

    private fun FinanceTransaction.reportMonth(mode: ReportDateMode): String =
        reportDate(mode).take(7)

    private fun String.parseIsoDateOrNull(): LocalDate? =
        runCatching { LocalDate.parse(this) }.getOrNull()

    private fun eur(value: Double, width: Int? = null): String {
        val text = "\u20AC%,.2f".format(value)
        return if (width == null) text else text.padStart(width + 1)
    }
}
