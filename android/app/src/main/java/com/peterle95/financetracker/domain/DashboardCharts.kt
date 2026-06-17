package com.peterle95.financetracker.domain

import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonElement
import kotlinx.serialization.json.JsonNull
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import java.time.DayOfWeek
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeParseException
import java.time.temporal.ChronoUnit

enum class ReportDateMode(val label: String) {
    BNPL("BNPL"),
    Normal("Normal"),
}

enum class BarBreakdownMode(val label: String) {
    Total("Total"),
    Categories("Categories"),
    Flexible("Flexible"),
    OverUnder("Over/Under"),
}

enum class ChartDisplayMode(val label: String) {
    Value("Euro"),
    Percentage("Percent"),
}

data class ChartEntry(
    val label: String,
    val value: Double,
)

data class ChartSeries(
    val label: String,
    val values: List<Double>,
)

data class PieChartModel(
    val title: String,
    val entries: List<ChartEntry>,
    val budgetInfo: List<String> = emptyList(),
)

data class HistoricalBarChartModel(
    val title: String,
    val labels: List<String>,
    val series: List<ChartSeries>,
    val displayMode: ChartDisplayMode,
)

data class LineChartModel(
    val title: String,
    val labels: List<String>,
    val series: List<ChartSeries>,
)

data class DayOfWeekChartModel(
    val title: String,
    val labels: List<String>,
    val averages: List<Double>,
    val counts: List<Int>,
)

data class SpendingPaceChartModel(
    val title: String,
    val days: List<Int>,
    val cumulativeSpending: List<Double>,
    val budgetPace: List<Double>,
    val monthlyBudget: Double,
)

object DashboardCharts {
    fun buildPieChart(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        month: String,
        rangeEndMonth: String? = null,
        type: TransactionType,
        includeFixedCosts: Boolean,
        includeBaseIncome: Boolean,
        showBudgetStatus: Boolean,
        sortByValue: Boolean,
        dateMode: ReportDateMode,
    ): PieChartModel {
        val months = if (rangeEndMonth.isNullOrBlank()) {
            listOf(month)
        } else {
            monthRange(month, rangeEndMonth)
        }
        val totals = linkedMapOf<String, Double>()

        if (type == TransactionType.Expense && includeFixedCosts) {
            val totalFixed = months.sumOf { activeFixedCosts(budgetSettings, it).sumOf { row -> row.numberValue("amount") } }
            if (totalFixed > 0.0) totals["Fixed Costs"] = totalFixed
        }
        if (type == TransactionType.Income && includeBaseIncome) {
            val totalBase = months.sumOf { activeMonthlyIncome(budgetSettings, it) }
            if (totalBase > 0.0) totals["Base Income"] = totalBase
        }

        val monthSet = months.toSet()
        transactions
            .filter { it.type == type && it.reportMonth(dateMode) in monthSet }
            .forEach { row ->
                val category = row.category.ifBlank { "Uncategorized" }
                totals[category] = (totals[category] ?: 0.0) + row.amount
            }

        val entries = totals.entries
            .map { ChartEntry(it.key, it.value) }
            .let { rows -> if (sortByValue) rows.sortedByDescending { it.value } else rows }

        val title = when {
            rangeEndMonth.isNullOrBlank() && type == TransactionType.Expense -> "Expenses for $month"
            rangeEndMonth.isNullOrBlank() -> "Incomes for $month"
            type == TransactionType.Expense -> "Expenses for ${months.first()} to ${months.last()}"
            else -> "Incomes for ${months.first()} to ${months.last()}"
        }

        val budgetInfo = if (
            showBudgetStatus &&
            rangeEndMonth.isNullOrBlank() &&
            type == TransactionType.Expense
        ) {
            buildBudgetStatus(entries, budgetSettings, transactions, month, dateMode)
        } else {
            emptyList()
        }

        return PieChartModel(title = title, entries = entries, budgetInfo = budgetInfo)
    }

    fun buildHistoricalBarChart(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        categories: CategoryState,
        numMonths: Int,
        endMonth: YearMonth,
        type: TransactionType,
        includeFixedCosts: Boolean,
        includeBaseIncome: Boolean,
        breakdownMode: BarBreakdownMode,
        displayMode: ChartDisplayMode,
        dateMode: ReportDateMode,
    ): HistoricalBarChartModel {
        val months = historicalMonths(numMonths, endMonth)
        val title = if (type == TransactionType.Expense) {
            "Historical Expenses for the Last ${months.size} Months"
        } else {
            "Historical Incomes for the Last ${months.size} Months"
        }

        val series = when (breakdownMode) {
            BarBreakdownMode.Total -> listOf(
                ChartSeries(
                    "Monthly Totals",
                    months.map { month ->
                        baseMonthlyValue(budgetSettings, month, type, includeFixedCosts, includeBaseIncome) +
                            transactions
                                .filter { it.type == type && it.reportMonth(dateMode) == month }
                                .sumOf { it.amount }
                    },
                ),
            )

            BarBreakdownMode.Categories -> categorySeries(
                transactions,
                budgetSettings,
                categories,
                months,
                type,
                includeFixedCosts,
                includeBaseIncome,
                displayMode,
                dateMode,
            )

            BarBreakdownMode.Flexible -> flexibleSeries(transactions, months, displayMode, dateMode)
            BarBreakdownMode.OverUnder -> overUnderSeries(transactions, budgetSettings, months, displayMode, dateMode)
        }

        return HistoricalBarChartModel(
            title = title,
            labels = months,
            series = series,
            displayMode = displayMode,
        )
    }

    fun buildLineChart(
        transactions: List<FinanceTransaction>,
        startMonth: String,
        endMonth: String,
        selectedCategories: Set<String>,
        dateMode: ReportDateMode,
    ): LineChartModel {
        val months = monthRange(startMonth, endMonth)
        val indexByMonth = months.withIndex().associate { it.value to it.index }
        val seriesByCategory = selectedCategories.associateWith { MutableList(months.size) { 0.0 } }

        transactions
            .filter { it.type == TransactionType.Expense }
            .forEach { row ->
                val monthIndex = indexByMonth[row.reportMonth(dateMode)] ?: return@forEach
                val values = seriesByCategory[row.category] ?: return@forEach
                values[monthIndex] += row.amount
            }

        val series = seriesByCategory
            .map { ChartSeries(it.key, it.value) }
            .filter { it.values.sum() > 0.0 }

        return LineChartModel(
            title = "Expense Categories from ${months.firstOrNull().orEmpty()} to ${months.lastOrNull().orEmpty()}",
            labels = months,
            series = series,
        )
    }

    fun buildDayOfWeekChart(
        transactions: List<FinanceTransaction>,
        monthsBack: Int,
        today: LocalDate,
        dateMode: ReportDateMode,
    ): DayOfWeekChartModel {
        val cutoff = today.minusMonths(monthsBack.coerceAtLeast(1).toLong())
        val totals = MutableList(7) { 0.0 }
        val uniqueDates = List(7) { mutableSetOf<String>() }

        transactions
            .filter { it.type == TransactionType.Expense }
            .forEach { row ->
                val dateText = row.reportDate(dateMode)
                val date = dateText.parseIsoDateOrNull() ?: return@forEach
                if (date < cutoff || date > today) return@forEach
                val index = date.dayOfWeek.mondayIndex()
                totals[index] += row.amount
                uniqueDates[index].add(dateText)
            }

        val counts = uniqueDates.map { it.size }
        val averages = totals.mapIndexed { index, total ->
            if (counts[index] == 0) 0.0 else total / counts[index]
        }

        return DayOfWeekChartModel(
            title = "Average Spending by Day of Week (last ${monthsBack.coerceAtLeast(1)} months)",
            labels = listOf("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"),
            averages = averages,
            counts = counts,
        )
    }

    fun buildSpendingPaceChart(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        month: String,
        today: LocalDate,
        dateMode: ReportDateMode,
    ): SpendingPaceChartModel {
        val yearMonth = YearMonth.parse(month)
        val daysInMonth = yearMonth.lengthOfMonth()
        val dailySavingsGoal = budgetSettings.numberValue("daily_savings_goal")
        val monthlyBudget = activeMonthlyIncome(budgetSettings, month) -
            activeFixedCosts(budgetSettings, month).sumOf { it.numberValue("amount") } -
            (dailySavingsGoal * daysInMonth)
        val dailySpend = mutableMapOf<Int, Double>()

        transactions
            .filter { it.type == TransactionType.Expense && it.reportMonth(dateMode) == month }
            .forEach { row ->
                val day = row.reportDate(dateMode).parseIsoDateOrNull()?.dayOfMonth ?: return@forEach
                dailySpend[day] = (dailySpend[day] ?: 0.0) + row.amount
            }

        val days = mutableListOf<Int>()
        val cumulative = mutableListOf<Double>()
        val pace = mutableListOf<Double>()
        var running = 0.0
        for (day in 1..daysInMonth) {
            val date = yearMonth.atDay(day)
            if (date > today) break
            running += dailySpend[day] ?: 0.0
            days += day
            cumulative += running
            pace += monthlyBudget * (day.toDouble() / daysInMonth.toDouble())
        }

        return SpendingPaceChartModel(
            title = "Spending Pace - $month",
            days = days,
            cumulativeSpending = cumulative,
            budgetPace = pace,
            monthlyBudget = monthlyBudget,
        )
    }

    fun activeFixedCosts(budgetSettings: JsonObject, month: String): List<JsonObject> {
        val costs = budgetSettings["fixed_costs"] as? JsonArray ?: return emptyList()
        return costs.mapNotNull { it as? JsonObject }
            .filter { isActiveForMonth(it, month) }
    }

    fun activeMonthlyIncome(budgetSettings: JsonObject, month: String): Double {
        val income = budgetSettings["monthly_income"] ?: return 0.0
        income.jsonPrimitiveOrNull()?.doubleOrNull?.let { return it }
        val rows = income as? JsonArray ?: return 0.0
        return rows.mapNotNull { it as? JsonObject }
            .filter { isActiveForMonth(it, month) }
            .sumOf { it.numberValue("amount") }
    }

    fun computeNetAvailableForSpending(budgetSettings: JsonObject, transactions: List<FinanceTransaction>, month: String, dateMode: ReportDateMode): Double {
        val baseIncome = activeMonthlyIncome(budgetSettings, month)
        val flexibleIncome = transactions
            .filter { it.type == TransactionType.Income && it.reportMonth(dateMode) == month }
            .sumOf { it.amount }
        val fixedCosts = activeFixedCosts(budgetSettings, month).sumOf { it.numberValue("amount") }
        val dailySavingsGoal = budgetSettings.numberValue("daily_savings_goal")
        val daysInMonth = runCatching { YearMonth.parse(month).lengthOfMonth() }.getOrDefault(30)
        return maxOf(baseIncome + flexibleIncome - fixedCosts - (dailySavingsGoal * daysInMonth), 0.0)
    }

    private fun categorySeries(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        categories: CategoryState,
        months: List<String>,
        type: TransactionType,
        includeFixedCosts: Boolean,
        includeBaseIncome: Boolean,
        displayMode: ChartDisplayMode,
        dateMode: ReportDateMode,
    ): List<ChartSeries> {
        val categoryNames = categories.forType(type)
        val valuesByCategory = categoryNames.associateWith { MutableList(months.size) { 0.0 } }.toMutableMap()
        val monthIndex = months.withIndex().associate { it.value to it.index }

        transactions
            .filter { it.type == type }
            .forEach { row ->
                val index = monthIndex[row.reportMonth(dateMode)] ?: return@forEach
                valuesByCategory.getOrPut(row.category.ifBlank { "Uncategorized" }) { MutableList(months.size) { 0.0 } }[index] += row.amount
            }

        if (type == TransactionType.Expense && includeFixedCosts) {
            valuesByCategory["Fixed Costs"] = months.map {
                activeFixedCosts(budgetSettings, it).sumOf { row -> row.numberValue("amount") }
            }.toMutableList()
        }
        if (type == TransactionType.Income && includeBaseIncome) {
            valuesByCategory["Base Income"] = months.map { activeMonthlyIncome(budgetSettings, it) }.toMutableList()
        }

        val nonEmpty = valuesByCategory
            .filterValues { it.sum() > 0.0 }
            .map { ChartSeries(it.key, it.value) }

        if (displayMode == ChartDisplayMode.Value) return nonEmpty

        val totalsByMonth = months.indices.map { index -> nonEmpty.sumOf { it.values[index] } }
        return nonEmpty.map { series ->
            series.copy(
                values = series.values.mapIndexed { index, value ->
                    if (totalsByMonth[index] > 0.0) (value / totalsByMonth[index]) * 100.0 else 0.0
                },
            )
        }
    }

    private fun flexibleSeries(
        transactions: List<FinanceTransaction>,
        months: List<String>,
        displayMode: ChartDisplayMode,
        dateMode: ReportDateMode,
    ): List<ChartSeries> {
        val income = months.map { month ->
            transactions.filter { it.type == TransactionType.Income && it.reportMonth(dateMode) == month }.sumOf { it.amount }
        }
        val costs = months.map { month ->
            transactions.filter { it.type == TransactionType.Expense && it.reportMonth(dateMode) == month }.sumOf { it.amount }
        }
        return if (displayMode == ChartDisplayMode.Percentage) {
            listOf(
                ChartSeries(
                    "Flexible Costs as % of Income",
                    income.zip(costs) { inc, cost -> if (inc > 0.0) (cost / inc) * 100.0 else if (cost > 0.0) 100.0 else 0.0 },
                ),
            )
        } else {
            listOf(
                ChartSeries("Flexible Income", income),
                ChartSeries("Flexible Costs", costs),
            )
        }
    }

    private fun overUnderSeries(
        transactions: List<FinanceTransaction>,
        budgetSettings: JsonObject,
        months: List<String>,
        displayMode: ChartDisplayMode,
        dateMode: ReportDateMode,
    ): List<ChartSeries> {
        val totalIncome = months.map { month ->
            activeMonthlyIncome(budgetSettings, month) +
                transactions.filter { it.type == TransactionType.Income && it.reportMonth(dateMode) == month }.sumOf { it.amount }
        }
        val totalExpenses = months.map { month ->
            activeFixedCosts(budgetSettings, month).sumOf { it.numberValue("amount") } +
                transactions.filter { it.type == TransactionType.Expense && it.reportMonth(dateMode) == month }.sumOf { it.amount }
        }
        return if (displayMode == ChartDisplayMode.Percentage) {
            listOf(ChartSeries("Net Result", totalIncome.zip(totalExpenses) { inc, exp -> inc - exp }))
        } else {
            listOf(
                ChartSeries("Total Income", totalIncome),
                ChartSeries("Total Expenses", totalExpenses),
            )
        }
    }

    private fun buildBudgetStatus(
        entries: List<ChartEntry>,
        budgetSettings: JsonObject,
        transactions: List<FinanceTransaction>,
        month: String,
        dateMode: ReportDateMode,
    ): List<String> {
        val expenseBudgets = budgetSettings["category_budgets"]
            ?.jsonObjectOrNull()
            ?.get("Expense")
            ?.jsonObjectOrNull()
            ?: return emptyList()
        val nav = computeNetAvailableForSpending(budgetSettings, transactions, month, dateMode)
        if (nav <= 0.0) return emptyList()

        return entries.mapNotNull { entry ->
            val percentLimit = expenseBudgets[entry.label]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0
            if (percentLimit <= 0.0) return@mapNotNull null
            val budgetAmount = (percentLimit / 100.0) * nav
            val usedPercent = if (budgetAmount > 0.0) (entry.value / budgetAmount) * 100.0 else 0.0
            val remaining = maxOf(budgetAmount - entry.value, 0.0)
            "${entry.label}: ${usedPercent.toInt()}% of budget, left ${"%.2f".format(remaining)}"
        }
    }

    private fun baseMonthlyValue(
        budgetSettings: JsonObject,
        month: String,
        type: TransactionType,
        includeFixedCosts: Boolean,
        includeBaseIncome: Boolean,
    ): Double =
        when {
            type == TransactionType.Expense && includeFixedCosts -> activeFixedCosts(budgetSettings, month).sumOf { it.numberValue("amount") }
            type == TransactionType.Income && includeBaseIncome -> activeMonthlyIncome(budgetSettings, month)
            else -> 0.0
        }

    private fun historicalMonths(numMonths: Int, endMonth: YearMonth): List<String> {
        val count = numMonths.coerceAtLeast(2)
        return (count - 1 downTo 0).map { endMonth.minusMonths(it.toLong()).toString() }
    }

    private fun monthRange(startMonth: String, endMonth: String): List<String> {
        var start = YearMonth.parse(startMonth)
        var end = YearMonth.parse(endMonth)
        if (start > end) start = end.also { end = start }
        val count = ChronoUnit.MONTHS.between(start, end).toInt()
        return (0..count).map { start.plusMonths(it.toLong()).toString() }
    }

    private fun FinanceTransaction.reportDate(mode: ReportDateMode): String =
        if (mode == ReportDateMode.BNPL) behaviorDate?.takeIf { it.isNotBlank() } ?: date else date

    private fun FinanceTransaction.reportMonth(mode: ReportDateMode): String =
        reportDate(mode).take(7)

    private fun isActiveForMonth(row: JsonObject, month: String): Boolean {
        val yearMonth = try {
            YearMonth.parse(month)
        } catch (_: DateTimeParseException) {
            return true
        }
        val monthStart = yearMonth.atDay(1)
        val monthEnd = yearMonth.atEndOfMonth()
        val start = row.stringValue("start_date")?.parseIsoDateOrNull() ?: LocalDate.of(2000, 1, 1)
        val end = row["end_date"].stringOrNull()?.parseIsoDateOrNull()
        return !start.isAfter(monthEnd) && (end == null || !end.isBefore(monthStart))
    }

    private fun DayOfWeek.mondayIndex(): Int =
        (value + 6) % 7

    private fun String.parseIsoDateOrNull(): LocalDate? =
        runCatching { LocalDate.parse(this) }.getOrNull()

    private fun JsonObject.numberValue(key: String): Double =
        this[key]?.jsonPrimitiveOrNull()?.doubleOrNull ?: 0.0

    private fun JsonObject.stringValue(key: String): String? = this[key].stringOrNull()

    private fun JsonElement?.stringOrNull(): String? =
        if (this == null || this is JsonNull) null else jsonPrimitiveOrNull()?.contentOrNull

    private fun JsonElement.jsonPrimitiveOrNull() = runCatching { jsonPrimitive }.getOrNull()

    private fun JsonElement.jsonObjectOrNull() = runCatching { jsonObject }.getOrNull()
}
