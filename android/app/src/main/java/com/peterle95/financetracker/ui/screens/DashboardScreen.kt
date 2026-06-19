package com.peterle95.financetracker.ui.screens

import android.graphics.Paint
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FilterChipDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.BarBreakdownMode
import com.peterle95.financetracker.domain.ChartDisplayMode
import com.peterle95.financetracker.domain.ChartEntry
import com.peterle95.financetracker.domain.ChartSeries
import com.peterle95.financetracker.domain.DashboardCharts
import com.peterle95.financetracker.domain.DayOfWeekChartModel
import com.peterle95.financetracker.domain.FinanceAggregator
import com.peterle95.financetracker.domain.HistoricalBarChartModel
import com.peterle95.financetracker.domain.LineChartModel
import com.peterle95.financetracker.domain.PieChartModel
import com.peterle95.financetracker.domain.ReportDateMode
import com.peterle95.financetracker.domain.SpendingPaceChartModel
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.CategoryDropdown
import com.peterle95.financetracker.ui.components.MetricCard
import com.peterle95.financetracker.ui.components.money
import java.time.LocalDate
import java.time.YearMonth
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

private enum class DashboardChartStyle(val label: String) {
    Pie("Pie Chart"),
    HistoricalBar("Historical Bar Chart"),
    Line("Line Chart"),
    DayOfWeek("Day-of-Week Heatmap"),
    SpendingPace("Spending Pace"),
}

private val chartColors = listOf(
    Color(0xFF2563EB),
    Color(0xFFDC2626),
    Color(0xFF16A34A),
    Color(0xFFF59E0B),
    Color(0xFF7C3AED),
    Color(0xFF0891B2),
    Color(0xFFDB2777),
    Color(0xFF65A30D),
    Color(0xFF9333EA),
    Color(0xFFEA580C),
)

private val chartViolet = Color(0xFF8250C4)

@Composable
fun DashboardScreen(
    viewModel: FinanceViewModel,
) {
    val transactions by viewModel.transactions.collectAsState()
    val budgetSettings by viewModel.budgetSettings.collectAsState()
    val categories by viewModel.categories.collectAsState()
    val nowMonth = remember { YearMonth.now() }
    val currentMonth = nowMonth.toString()
    val defaultStartMonth = remember { nowMonth.minusMonths(3).toString() }
    var dashboardMonth by remember { mutableStateOf(currentMonth) }
    val dashboard = remember(transactions, budgetSettings, dashboardMonth) {
        val parsedMonth = runCatching { YearMonth.parse(dashboardMonth) }.getOrDefault(nowMonth)
        FinanceAggregator.buildDashboardSummary(transactions, budgetSettings, parsedMonth)
    }

    var chartStyle by remember { mutableStateOf(DashboardChartStyle.Pie) }
    var reportDateMode by remember { mutableStateOf(ReportDateMode.BNPL) }
    var dataType by remember { mutableStateOf(TransactionType.Expense) }

    var pieMonth by remember { mutableStateOf(currentMonth) }
    var pieRange by remember { mutableStateOf(false) }
    var pieStartMonth by remember { mutableStateOf(defaultStartMonth) }
    var pieEndMonth by remember { mutableStateOf(currentMonth) }
    var pieDisplayMode by remember { mutableStateOf(ChartDisplayMode.Value) }
    var sortPie by remember { mutableStateOf(true) }
    var showBudgetStatus by remember { mutableStateOf(false) }

    var includeFixedCosts by remember { mutableStateOf(false) }
    var includeBaseIncome by remember { mutableStateOf(false) }
    var barMonths by remember { mutableStateOf("6") }
    var showBarLabels by remember { mutableStateOf(false) }
    var barBreakdownMode by remember { mutableStateOf(BarBreakdownMode.Total) }
    var barDisplayMode by remember { mutableStateOf(ChartDisplayMode.Value) }

    var lineStartMonth by remember { mutableStateOf(defaultStartMonth) }
    var lineEndMonth by remember { mutableStateOf(currentMonth) }
    var selectedLineCategories by remember { mutableStateOf<Set<String>>(emptySet()) }

    var dowMonths by remember { mutableStateOf("3") }
    var paceMonth by remember { mutableStateOf(currentMonth) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Dashboard", style = MaterialTheme.typography.headlineMedium)
                Text(dashboard.currentMonth, style = MaterialTheme.typography.titleMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = dashboardMonth,
                        onValueChange = { dashboardMonth = it },
                        label = { Text("Month") },
                        singleLine = true,
                        modifier = Modifier.weight(1f),
                    )
                    OutlinedButton(onClick = { runCatching { YearMonth.parse(dashboardMonth).minusMonths(1).toString() }.onSuccess { dashboardMonth = it } }) {
                        Text("Prev")
                    }
                    OutlinedButton(onClick = { runCatching { YearMonth.parse(dashboardMonth).plusMonths(1).toString() }.onSuccess { dashboardMonth = it } }) {
                        Text("Next")
                    }
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Income", money(dashboard.income), Modifier.weight(1f))
                MetricCard("Expenses", money(dashboard.expenses), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Net", money(dashboard.net), Modifier.weight(1f))
                dashboard.balanceEstimate?.let {
                    MetricCard("Net Worth", money(it), Modifier.weight(1f))
                } ?: MetricCard("Daily Budget", money(dashboard.remainingDailyBudget), Modifier.weight(1f))
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                MetricCard("Daily Budget", money(dashboard.remainingDailyBudget), Modifier.weight(1f))
                MetricCard("Top Categories", dashboard.topExpenseCategories.size.toString(), Modifier.weight(1f))
            }
        }
        if (dashboard.topExpenseCategories.isNotEmpty()) {
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(14.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp),
                    ) {
                        Text("Top Expense Categories", style = MaterialTheme.typography.titleLarge)
                        dashboard.topExpenseCategories.forEach { (category, amount) ->
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                            ) {
                                Text(category)
                                Text(money(amount), style = MaterialTheme.typography.labelLarge)
                            }
                        }
                    }
                }
            }
        }
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp),
                ) {
                    Text("Charts", style = MaterialTheme.typography.titleLarge)
                    MaterialTheme(
                        colorScheme = MaterialTheme.colorScheme.copy(primary = chartViolet),
                    ) {
                        CategoryDropdown(
                            label = "Chart Style",
                            selected = chartStyle.label,
                            categories = DashboardChartStyle.entries.map { it.label },
                            onSelected = { selected ->
                                chartStyle = DashboardChartStyle.entries.first { it.label == selected }
                            },
                        )
                    }
                    ChipRow(
                        label = "Transaction Filter",
                        options = ReportDateMode.entries.toList(),
                        selected = reportDateMode,
                        labelFor = { it.label },
                        onSelected = { reportDateMode = it },
                    )
                    if (chartStyle == DashboardChartStyle.Pie || chartStyle == DashboardChartStyle.HistoricalBar) {
                        ChipRow(
                            label = "Data Type",
                            options = TransactionType.entries.toList(),
                            selected = dataType,
                            labelFor = { it.label },
                            onSelected = { dataType = it },
                        )
                    }

                    when (chartStyle) {
                        DashboardChartStyle.Pie -> {
                            PieControls(
                                pieRange = pieRange,
                                onPieRangeChange = { pieRange = it },
                                pieMonth = pieMonth,
                                onPieMonthChange = { pieMonth = it },
                                pieStartMonth = pieStartMonth,
                                onPieStartMonthChange = { pieStartMonth = it },
                                pieEndMonth = pieEndMonth,
                                onPieEndMonthChange = { pieEndMonth = it },
                                displayMode = pieDisplayMode,
                                onDisplayModeChange = { pieDisplayMode = it },
                                sortPie = sortPie,
                                onSortPieChange = { sortPie = it },
                                includeFixedCosts = includeFixedCosts,
                                onIncludeFixedCostsChange = { includeFixedCosts = it },
                                includeBaseIncome = includeBaseIncome,
                                onIncludeBaseIncomeChange = { includeBaseIncome = it },
                                showBudgetStatus = showBudgetStatus,
                                onShowBudgetStatusChange = { showBudgetStatus = it },
                                dataType = dataType,
                            )
                            ChartResult(
                                result = runCatching {
                                    DashboardCharts.buildPieChart(
                                        transactions = transactions,
                                        budgetSettings = budgetSettings,
                                        month = if (pieRange) pieStartMonth else pieMonth,
                                        rangeEndMonth = if (pieRange) pieEndMonth else null,
                                        type = dataType,
                                        includeFixedCosts = includeFixedCosts,
                                        includeBaseIncome = includeBaseIncome,
                                        showBudgetStatus = showBudgetStatus,
                                        sortByValue = sortPie,
                                        dateMode = reportDateMode,
                                    )
                                },
                            ) { PieChart(it, pieDisplayMode) }
                        }

                        DashboardChartStyle.HistoricalBar -> {
                            BarControls(
                                months = barMonths,
                                onMonthsChange = { barMonths = it },
                                showLabels = showBarLabels,
                                onShowLabelsChange = { showBarLabels = it },
                                breakdownMode = barBreakdownMode,
                                onBreakdownModeChange = { barBreakdownMode = it },
                                displayMode = barDisplayMode,
                                onDisplayModeChange = { barDisplayMode = it },
                                includeFixedCosts = includeFixedCosts,
                                onIncludeFixedCostsChange = { includeFixedCosts = it },
                                includeBaseIncome = includeBaseIncome,
                                onIncludeBaseIncomeChange = { includeBaseIncome = it },
                                dataType = dataType,
                            )
                            ChartResult(
                                result = runCatching {
                                    DashboardCharts.buildHistoricalBarChart(
                                        transactions = transactions,
                                        budgetSettings = budgetSettings,
                                        categories = categories,
                                        numMonths = barMonths.toIntOrNull()?.coerceAtLeast(2) ?: 6,
                                        endMonth = nowMonth,
                                        type = dataType,
                                        includeFixedCosts = includeFixedCosts,
                                        includeBaseIncome = includeBaseIncome,
                                        breakdownMode = barBreakdownMode,
                                        displayMode = barDisplayMode,
                                        dateMode = reportDateMode,
                                    )
                                },
                            ) { BarChart(it, barBreakdownMode, showBarLabels) }
                        }

                        DashboardChartStyle.Line -> {
                            LineControls(
                                startMonth = lineStartMonth,
                                onStartMonthChange = { lineStartMonth = it },
                                endMonth = lineEndMonth,
                                onEndMonthChange = { lineEndMonth = it },
                                categories = categories.expenses,
                                selectedCategories = selectedLineCategories,
                                onToggleCategory = { category ->
                                    selectedLineCategories = if (category in selectedLineCategories) {
                                        selectedLineCategories - category
                                    } else {
                                        selectedLineCategories + category
                                    }
                                },
                            )
                            ChartResult(
                                result = runCatching {
                                    DashboardCharts.buildLineChart(
                                        transactions = transactions,
                                        startMonth = lineStartMonth,
                                        endMonth = lineEndMonth,
                                        selectedCategories = selectedLineCategories,
                                        dateMode = reportDateMode,
                                    )
                                },
                            ) { LineChart(it) }
                        }

                        DashboardChartStyle.DayOfWeek -> {
                            SmallNumberField("Months of History", dowMonths, onValueChange = { dowMonths = it })
                            ChartResult(
                                result = runCatching {
                                    DashboardCharts.buildDayOfWeekChart(
                                        transactions = transactions,
                                        monthsBack = dowMonths.toIntOrNull()?.coerceAtLeast(1) ?: 3,
                                        today = LocalDate.now(),
                                        dateMode = reportDateMode,
                                    )
                                },
                            ) { DayOfWeekChart(it) }
                        }

                        DashboardChartStyle.SpendingPace -> {
                            SmallNumberField("Month", paceMonth, onValueChange = { paceMonth = it })
                            ChartResult(
                                result = runCatching {
                                    DashboardCharts.buildSpendingPaceChart(
                                        transactions = transactions,
                                        budgetSettings = budgetSettings,
                                        month = paceMonth,
                                        today = LocalDate.now(),
                                        dateMode = reportDateMode,
                                    )
                                },
                            ) { SpendingPaceChart(it) }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PieControls(
    pieRange: Boolean,
    onPieRangeChange: (Boolean) -> Unit,
    pieMonth: String,
    onPieMonthChange: (String) -> Unit,
    pieStartMonth: String,
    onPieStartMonthChange: (String) -> Unit,
    pieEndMonth: String,
    onPieEndMonthChange: (String) -> Unit,
    displayMode: ChartDisplayMode,
    onDisplayModeChange: (ChartDisplayMode) -> Unit,
    sortPie: Boolean,
    onSortPieChange: (Boolean) -> Unit,
    includeFixedCosts: Boolean,
    onIncludeFixedCostsChange: (Boolean) -> Unit,
    includeBaseIncome: Boolean,
    onIncludeBaseIncomeChange: (Boolean) -> Unit,
    showBudgetStatus: Boolean,
    onShowBudgetStatusChange: (Boolean) -> Unit,
    dataType: TransactionType,
) {
    ChipRow(
        label = "Period",
        options = listOf(false, true),
        selected = pieRange,
        labelFor = { if (it) "Range" else "Month" },
        onSelected = onPieRangeChange,
    )
    if (pieRange) {
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            SmallNumberField("From", pieStartMonth, onPieStartMonthChange, Modifier.weight(1f))
            SmallNumberField("To", pieEndMonth, onPieEndMonthChange, Modifier.weight(1f))
        }
    } else {
        SmallNumberField("Month", pieMonth, onPieMonthChange)
    }
    ChipRow(
        label = "Display",
        options = ChartDisplayMode.entries.toList(),
        selected = displayMode,
        labelFor = { if (it == ChartDisplayMode.Value) "Euro" else "Percent" },
        onSelected = onDisplayModeChange,
    )
    BooleanOption("Sort by Value", sortPie, onSortPieChange)
    IncludeBaseOptions(
        type = dataType,
        includeFixedCosts = includeFixedCosts,
        onIncludeFixedCostsChange = onIncludeFixedCostsChange,
        includeBaseIncome = includeBaseIncome,
        onIncludeBaseIncomeChange = onIncludeBaseIncomeChange,
    )
    if (dataType == TransactionType.Expense && !pieRange) {
        BooleanOption("Show Budget Status", showBudgetStatus, onShowBudgetStatusChange)
    }
}

@Composable
private fun BarControls(
    months: String,
    onMonthsChange: (String) -> Unit,
    showLabels: Boolean,
    onShowLabelsChange: (Boolean) -> Unit,
    breakdownMode: BarBreakdownMode,
    onBreakdownModeChange: (BarBreakdownMode) -> Unit,
    displayMode: ChartDisplayMode,
    onDisplayModeChange: (ChartDisplayMode) -> Unit,
    includeFixedCosts: Boolean,
    onIncludeFixedCostsChange: (Boolean) -> Unit,
    includeBaseIncome: Boolean,
    onIncludeBaseIncomeChange: (Boolean) -> Unit,
    dataType: TransactionType,
) {
    SmallNumberField("Number of Months", months, onMonthsChange)
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        OutlinedButton(
            onClick = {
                val next = when (breakdownMode) {
                    BarBreakdownMode.Total -> BarBreakdownMode.Categories
                    BarBreakdownMode.Categories -> BarBreakdownMode.Flexible
                    BarBreakdownMode.Flexible -> BarBreakdownMode.OverUnder
                    BarBreakdownMode.OverUnder -> BarBreakdownMode.Total
                }
                onBreakdownModeChange(next)
            },
            colors = ButtonDefaults.outlinedButtonColors(contentColor = chartViolet),
            border = BorderStroke(1.dp, chartViolet),
        ) {
            Text("View: ${breakdownMode.label}")
        }
        OutlinedButton(
            onClick = {
                onDisplayModeChange(
                    if (displayMode == ChartDisplayMode.Value) ChartDisplayMode.Percentage else ChartDisplayMode.Value,
                )
            },
            colors = ButtonDefaults.outlinedButtonColors(contentColor = chartViolet),
            border = BorderStroke(1.dp, chartViolet),
        ) {
            Text("Display: ${displayMode.label}")
        }
    }
    BooleanOption("Show Bar Labels", showLabels, onShowLabelsChange)
    IncludeBaseOptions(
        type = dataType,
        includeFixedCosts = includeFixedCosts,
        onIncludeFixedCostsChange = onIncludeFixedCostsChange,
        includeBaseIncome = includeBaseIncome,
        onIncludeBaseIncomeChange = onIncludeBaseIncomeChange,
    )
}

@Composable
private fun LineControls(
    startMonth: String,
    onStartMonthChange: (String) -> Unit,
    endMonth: String,
    onEndMonthChange: (String) -> Unit,
    categories: List<String>,
    selectedCategories: Set<String>,
    onToggleCategory: (String) -> Unit,
) {
    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        SmallNumberField("From", startMonth, onStartMonthChange, Modifier.weight(1f))
        SmallNumberField("To", endMonth, onEndMonthChange, Modifier.weight(1f))
    }
    Text("Categories (${selectedCategories.size})", style = MaterialTheme.typography.labelLarge)
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        categories.forEach { category ->
            FilterChip(
                selected = category in selectedCategories,
                onClick = { onToggleCategory(category) },
                colors = chartFilterChipColors(),
                label = { Text(category) },
            )
        }
    }
}

@Composable
private fun IncludeBaseOptions(
    type: TransactionType,
    includeFixedCosts: Boolean,
    onIncludeFixedCostsChange: (Boolean) -> Unit,
    includeBaseIncome: Boolean,
    onIncludeBaseIncomeChange: (Boolean) -> Unit,
) {
    if (type == TransactionType.Expense) {
        BooleanOption("Include Fixed Costs", includeFixedCosts, onIncludeFixedCostsChange)
    } else {
        BooleanOption("Include Base Income", includeBaseIncome, onIncludeBaseIncomeChange)
    }
}

@Composable
private fun <T> ChipRow(
    label: String,
    options: List<T>,
    selected: T,
    labelFor: (T) -> String,
    onSelected: (T) -> Unit,
) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        Text(label, style = MaterialTheme.typography.labelLarge)
        Row(
            modifier = Modifier.horizontalScroll(rememberScrollState()),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            options.forEach { option ->
                FilterChip(
                    selected = option == selected,
                    onClick = { onSelected(option) },
                    colors = chartFilterChipColors(),
                    label = { Text(labelFor(option)) },
                )
            }
        }
    }
}

@Composable
private fun chartFilterChipColors() = FilterChipDefaults.filterChipColors(
    labelColor = chartViolet,
    selectedContainerColor = chartViolet,
    selectedLabelColor = Color.White,
)

@Composable
private fun BooleanOption(label: String, checked: Boolean, onCheckedChange: (Boolean) -> Unit) {
    Row(
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Checkbox(checked = checked, onCheckedChange = onCheckedChange)
        Text(label, style = MaterialTheme.typography.labelLarge)
    }
}

@Composable
private fun SmallNumberField(
    label: String,
    value: String,
    onValueChange: (String) -> Unit,
    modifier: Modifier = Modifier,
) {
    OutlinedTextField(
        value = value,
        onValueChange = onValueChange,
        label = { Text(label) },
        singleLine = true,
        modifier = modifier.fillMaxWidth(),
    )
}

@Composable
private fun <T> ChartResult(result: Result<T>, content: @Composable (T) -> Unit) {
    val value = result.getOrNull()
    if (value != null) {
        content(value)
    } else {
        Text(result.exceptionOrNull()?.message ?: "Could not build chart.", color = MaterialTheme.colorScheme.error)
    }
}

@Composable
private fun PieChart(model: PieChartModel, displayMode: ChartDisplayMode) {
    if (model.entries.isEmpty()) {
        Text("No data for the selected period.")
        return
    }
    Text(model.title, style = MaterialTheme.typography.titleMedium)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(260.dp),
    ) {
        val total = model.entries.sumOf { it.value }
        if (total <= 0.0) return@Canvas
        val diameter = min(size.width, size.height) * 0.78f
        val topLeft = Offset((size.width - diameter) / 2f, (size.height - diameter) / 2f)
        var startAngle = -90f
        model.entries.forEachIndexed { index, entry ->
            val sweep = (entry.value / total * 360.0).toFloat()
            drawArc(
                color = chartColors[index % chartColors.size],
                startAngle = startAngle,
                sweepAngle = sweep,
                useCenter = true,
                topLeft = topLeft,
                size = Size(diameter, diameter),
            )
            startAngle += sweep
        }
    }
    Legend(entries = model.entries, displayMode = displayMode)
    model.budgetInfo.forEach {
        Text(it, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}

@Composable
private fun BarChart(model: HistoricalBarChartModel, breakdownMode: BarBreakdownMode, showLabels: Boolean) {
    if (model.series.isEmpty() || model.series.all { series -> series.values.all { it == 0.0 } }) {
        Text("No data for the selected period.")
        return
    }
    Text(model.title, style = MaterialTheme.typography.titleMedium)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(280.dp),
    ) {
        drawBarSeries(
            labels = model.labels,
            series = model.series,
            stacked = breakdownMode == BarBreakdownMode.Categories,
            showLabels = showLabels,
            displayMode = model.displayMode,
        )
    }
    SeriesLegend(model.series)
}

@Composable
private fun LineChart(model: LineChartModel) {
    if (model.series.isEmpty()) {
        Text("Select one or more categories with data.")
        return
    }
    Text(model.title, style = MaterialTheme.typography.titleMedium)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(280.dp),
    ) {
        drawLineSeries(model.labels, model.series)
    }
    SeriesLegend(model.series)
}

@Composable
private fun DayOfWeekChart(model: DayOfWeekChartModel) {
    if (model.averages.all { it == 0.0 }) {
        Text("No spending data for this range.")
        return
    }
    Text(model.title, style = MaterialTheme.typography.titleMedium)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(260.dp),
    ) {
        drawBarSeries(
            labels = model.labels,
            series = listOf(ChartSeries("Average", model.averages)),
            stacked = false,
            showLabels = true,
            displayMode = ChartDisplayMode.Value,
        )
    }
    Text(
        model.labels.zip(model.counts).joinToString("  ") { "${it.first}: ${it.second}d" },
        style = MaterialTheme.typography.bodySmall,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

@Composable
private fun SpendingPaceChart(model: SpendingPaceChartModel) {
    if (model.days.isEmpty()) {
        Text("No data yet for this month.")
        return
    }
    Text(model.title, style = MaterialTheme.typography.titleMedium)
    Text("Monthly budget: ${money(model.monthlyBudget)}", style = MaterialTheme.typography.bodySmall)
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(280.dp),
    ) {
        drawLineSeries(
            labels = model.days.map { it.toString() },
            series = listOf(
                ChartSeries("Actual Spending", model.cumulativeSpending),
                ChartSeries("Budget Pace", model.budgetPace),
            ),
        )
    }
    SeriesLegend(
        listOf(
            ChartSeries("Actual Spending", model.cumulativeSpending),
            ChartSeries("Budget Pace", model.budgetPace),
        ),
    )
}

@Composable
private fun Legend(entries: List<ChartEntry>, displayMode: ChartDisplayMode) {
    val total = entries.sumOf { it.value }.takeIf { it > 0.0 } ?: 1.0
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        entries.forEachIndexed { index, entry ->
            LegendRow(
                color = chartColors[index % chartColors.size],
                label = entry.label,
                value = if (displayMode == ChartDisplayMode.Percentage) {
                    "${entry.value / total * 100.0}".formatOneDecimal() + "%"
                } else {
                    money(entry.value)
                },
            )
        }
    }
}

@Composable
private fun SeriesLegend(series: List<ChartSeries>) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        series.forEachIndexed { index, item ->
            LegendRow(
                color = chartColors[index % chartColors.size],
                label = item.label,
                value = "",
            )
        }
    }
}

@Composable
private fun LegendRow(color: Color, label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        Box(
            modifier = Modifier
                .size(12.dp)
                .background(color),
        )
        Text(label, modifier = Modifier.weight(1f))
        if (value.isNotBlank()) Text(value, style = MaterialTheme.typography.labelLarge)
    }
}

private fun DrawScope.drawBarSeries(
    labels: List<String>,
    series: List<ChartSeries>,
    stacked: Boolean,
    showLabels: Boolean,
    displayMode: ChartDisplayMode,
) {
    val allValues = series.flatMap { it.values } + 0.0
    val minValue = min(0.0, allValues.minOrNull() ?: 0.0)
    val maxValue = max(0.0, allValues.maxOrNull() ?: 1.0)
    val range = (maxValue - minValue).takeIf { it > 0.0 } ?: 1.0
    val left = 46f
    val right = size.width - 12f
    val top = 18f
    val bottom = size.height - 38f
    val chartWidth = right - left
    val chartHeight = bottom - top
    val zeroY = top + ((maxValue - 0.0) / range).toFloat() * chartHeight

    fun y(value: Double): Float = top + ((maxValue - value) / range).toFloat() * chartHeight

    drawLine(Color(0xFF9CA3AF), Offset(left, top), Offset(left, bottom), strokeWidth = 1.5f)
    drawLine(Color(0xFF9CA3AF), Offset(left, zeroY), Offset(right, zeroY), strokeWidth = 1.5f)
    drawText(axisValue(maxValue, displayMode), 4f, top + 10f, Color(0xFF6B7280), 24f, Paint.Align.LEFT)
    if (minValue < 0.0) drawText(axisValue(minValue, displayMode), 4f, bottom, Color(0xFF6B7280), 24f, Paint.Align.LEFT)

    val count = labels.size.coerceAtLeast(1)
    val slot = chartWidth / count
    labels.forEachIndexed { monthIndex, label ->
        val center = left + slot * monthIndex + slot / 2f
        if (labels.size <= 8 || monthIndex % 2 == 0) {
            drawText(label, center, size.height - 10f, Color(0xFF6B7280), 22f, Paint.Align.CENTER)
        }
    }

    if (stacked) {
        labels.indices.forEach { monthIndex ->
            var positiveBase = 0.0
            var negativeBase = 0.0
            val barWidth = slot * 0.56f
            val x = left + slot * monthIndex + (slot - barWidth) / 2f
            series.forEachIndexed { seriesIndex, item ->
                val value = item.values.getOrElse(monthIndex) { 0.0 }
                val start = if (value >= 0.0) positiveBase else negativeBase
                val end = start + value
                if (value >= 0.0) positiveBase = end else negativeBase = end
                drawRect(
                    color = chartColors[seriesIndex % chartColors.size],
                    topLeft = Offset(x, min(y(start), y(end))),
                    size = Size(barWidth, abs(y(end) - y(start)).coerceAtLeast(1f)),
                )
            }
        }
    } else {
        val seriesCount = series.size.coerceAtLeast(1)
        labels.indices.forEach { monthIndex ->
            val groupWidth = slot * 0.68f
            val barWidth = groupWidth / seriesCount
            val groupStart = left + slot * monthIndex + (slot - groupWidth) / 2f
            series.forEachIndexed { seriesIndex, item ->
                val value = item.values.getOrElse(monthIndex) { 0.0 }
                val x = groupStart + barWidth * seriesIndex
                val yValue = y(value)
                drawRect(
                    color = chartColors[seriesIndex % chartColors.size],
                    topLeft = Offset(x + 1f, min(yValue, zeroY)),
                    size = Size((barWidth - 2f).coerceAtLeast(1f), abs(zeroY - yValue).coerceAtLeast(1f)),
                )
                if (showLabels) {
                    val label = if (displayMode == ChartDisplayMode.Percentage) {
                        "${value}".formatOneDecimal() + "%"
                    } else {
                        money(value)
                    }
                    drawText(label, x + barWidth / 2f, min(yValue, zeroY) - 4f, Color(0xFF374151), 20f, Paint.Align.CENTER)
                }
            }
        }
    }
}

private fun DrawScope.drawLineSeries(labels: List<String>, series: List<ChartSeries>) {
    val allValues = series.flatMap { it.values } + 0.0
    val minValue = min(0.0, allValues.minOrNull() ?: 0.0)
    val maxValue = max(0.0, allValues.maxOrNull() ?: 1.0)
    val range = (maxValue - minValue).takeIf { it > 0.0 } ?: 1.0
    val left = 46f
    val right = size.width - 12f
    val top = 18f
    val bottom = size.height - 38f
    val chartWidth = right - left
    val chartHeight = bottom - top
    val zeroY = top + ((maxValue - 0.0) / range).toFloat() * chartHeight

    fun x(index: Int): Float =
        if (labels.size <= 1) left + chartWidth / 2f else left + (index.toFloat() / (labels.size - 1).toFloat()) * chartWidth

    fun y(value: Double): Float = top + ((maxValue - value) / range).toFloat() * chartHeight

    drawLine(Color(0xFF9CA3AF), Offset(left, top), Offset(left, bottom), strokeWidth = 1.5f)
    drawLine(Color(0xFF9CA3AF), Offset(left, zeroY), Offset(right, zeroY), strokeWidth = 1.5f)
    drawText(money(maxValue), 4f, top + 10f, Color(0xFF6B7280), 24f, Paint.Align.LEFT)
    if (minValue < 0.0) drawText(money(minValue), 4f, bottom, Color(0xFF6B7280), 24f, Paint.Align.LEFT)

    labels.forEachIndexed { index, label ->
        if (labels.size <= 8 || index % 2 == 0) {
            drawText(label, x(index), size.height - 10f, Color(0xFF6B7280), 22f, Paint.Align.CENTER)
        }
    }

    series.forEachIndexed { seriesIndex, item ->
        val color = chartColors[seriesIndex % chartColors.size]
        item.values.indices.drop(1).forEach { index ->
            drawLine(
                color = color,
                start = Offset(x(index - 1), y(item.values[index - 1])),
                end = Offset(x(index), y(item.values[index])),
                strokeWidth = 4f,
            )
        }
        item.values.forEachIndexed { index, value ->
            drawCircle(color = color, radius = 5f, center = Offset(x(index), y(value)))
        }
    }
}

private fun DrawScope.drawText(
    text: String,
    x: Float,
    y: Float,
    color: Color,
    textSize: Float,
    align: Paint.Align,
) {
    drawContext.canvas.nativeCanvas.drawText(
        text,
        x,
        y,
        Paint().apply {
            this.color = color.toArgb()
            this.textSize = textSize
            this.textAlign = align
            isAntiAlias = true
        },
    )
}

private fun String.formatOneDecimal(): String =
    toDoubleOrNull()?.let { "%.1f".format(it) } ?: this

private fun axisValue(value: Double, displayMode: ChartDisplayMode): String =
    if (displayMode == ChartDisplayMode.Percentage) {
        "${value}".formatOneDecimal() + "%"
    } else {
        money(value)
    }
