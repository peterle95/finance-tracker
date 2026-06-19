package com.peterle95.financetracker.ui.screens

import android.content.Intent
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.KeyboardArrowDown
import androidx.compose.material.icons.outlined.KeyboardArrowUp
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.Checkbox
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.BudgetMath
import com.peterle95.financetracker.domain.BudgetReport
import com.peterle95.financetracker.domain.CategoryBudgetStatus
import com.peterle95.financetracker.domain.FixedCost
import com.peterle95.financetracker.domain.IncomeSource
import com.peterle95.financetracker.domain.todayIsoDate
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.MetricCard
import com.peterle95.financetracker.ui.components.money
import java.time.YearMonth
import kotlin.math.max
import kotlin.math.min

@Composable
fun BudgetScreen(viewModel: FinanceViewModel) {
    val settings by viewModel.budgetSettingsModel.collectAsState()
    val transactions by viewModel.transactions.collectAsState()
    val categories by viewModel.categories.collectAsState()
    val context = LocalContext.current
    var month by remember { mutableStateOf(YearMonth.now().toString()) }
    var includeCarryover by remember { mutableStateOf(false) }
    var showDailyBreakdown by remember { mutableStateOf(false) }
    var showOverviewSection by remember { mutableStateOf(false) }
    var showReportSection by remember { mutableStateOf(false) }
    var showChartSection by remember { mutableStateOf(false) }
    var showBalancesSection by remember { mutableStateOf(false) }
    var showSavingsSection by remember { mutableStateOf(false) }
    var showIncomeSection by remember { mutableStateOf(false) }
    var showFixedCostsSection by remember { mutableStateOf(false) }
    var showCategorySection by remember { mutableStateOf(false) }
    val report = remember(settings, transactions, month, includeCarryover) {
        BudgetMath.generateDailyBudgetReport(
            settings = settings,
            transactions = transactions,
            month = month,
            includeNegativeCarryover = includeCarryover,
        )
    }
    val categoryStatuses = remember(settings, transactions, categories, month) {
        BudgetMath.categoryBudgetStatuses(settings, transactions, categories.expenses, month)
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Budget", style = MaterialTheme.typography.headlineMedium)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = month,
                        onValueChange = { month = it },
                        label = { Text("Month") },
                        singleLine = true,
                        modifier = Modifier.weight(1f),
                    )
                    OutlinedButton(onClick = { runCatching { YearMonth.parse(month).minusMonths(1).toString() }.onSuccess { month = it } }) {
                        Text("Prev")
                    }
                    OutlinedButton(onClick = { runCatching { YearMonth.parse(month).plusMonths(1).toString() }.onSuccess { month = it } }) {
                        Text("Next")
                    }
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = includeCarryover, onCheckedChange = { includeCarryover = it })
                    Text("Include previous month deficit", style = MaterialTheme.typography.labelLarge)
                }
            }
        }
        item {
            BudgetSectionButton(
                title = "Overview",
                expanded = showOverviewSection,
                onClick = { showOverviewSection = !showOverviewSection },
            )
        }
        if (showOverviewSection) {
            item { BudgetOverview(report) }
        }
        item {
            BudgetSectionButton(
                title = "Daily Budget Report",
                expanded = showReportSection,
                onClick = { showReportSection = !showReportSection },
            )
        }
        if (showReportSection) {
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(14.dp),
                        verticalArrangement = Arrangement.spacedBy(10.dp),
                    ) {
                        Text("Daily Budget Report", style = MaterialTheme.typography.titleLarge)
                        Text(report.statusTitle, style = MaterialTheme.typography.titleMedium)
                        Text(report.statusDetail, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            Button(onClick = { showDailyBreakdown = !showDailyBreakdown }) {
                                Text(if (showDailyBreakdown) "Hide Daily Breakdown" else "Show Daily Breakdown")
                            }
                            OutlinedButton(
                                onClick = {
                                    val intent = Intent(Intent.ACTION_SEND).apply {
                                        type = "text/plain"
                                        putExtra(Intent.EXTRA_SUBJECT, "Budget report ${report.month}")
                                        putExtra(Intent.EXTRA_TEXT, report.textReport)
                                    }
                                    context.startActivity(Intent.createChooser(intent, "Share budget report"))
                                },
                            ) {
                                Text("Share")
                            }
                        }
                        if (showDailyBreakdown) {
                            Text(
                                report.textReport,
                                style = MaterialTheme.typography.bodySmall,
                                modifier = Modifier.horizontalScroll(rememberScrollState()),
                            )
                        }
                    }
                }
            }
        }
        item {
            BudgetSectionButton(
                title = "Budget Depletion",
                expanded = showChartSection,
                onClick = { showChartSection = !showChartSection },
            )
        }
        if (showChartSection) {
            item { BudgetDepletionChart(report) }
        }
        item {
            BudgetSectionButton(
                title = "Balances",
                expanded = showBalancesSection,
                onClick = { showBalancesSection = !showBalancesSection },
            )
        }
        if (showBalancesSection) {
            item { BalanceEditor(settings.balances, viewModel) }
        }
        item {
            BudgetSectionButton(
                title = "Daily Savings Goal",
                expanded = showSavingsSection,
                onClick = { showSavingsSection = !showSavingsSection },
            )
        }
        if (showSavingsSection) {
            item { DailySavingsEditor(settings.dailySavingsGoal, viewModel) }
        }
        item {
            BudgetSectionButton(
                title = "Income Sources",
                expanded = showIncomeSection,
                onClick = { showIncomeSection = !showIncomeSection },
            )
        }
        if (showIncomeSection) {
            item { IncomeSourceEditor(viewModel) }
            items(settings.monthlyIncome, key = { it.key }) { source ->
                IncomeSourceRow(source, viewModel)
            }
        }
        item {
            BudgetSectionButton(
                title = "Fixed Costs",
                expanded = showFixedCostsSection,
                onClick = { showFixedCostsSection = !showFixedCostsSection },
            )
        }
        if (showFixedCostsSection) {
            item { FixedCostEditor(viewModel) }
            items(settings.fixedCosts, key = { it.key }) { cost ->
                FixedCostRow(cost, viewModel)
            }
        }
        item {
            BudgetSectionButton(
                title = "Category Budget Limits",
                expanded = showCategorySection,
                onClick = { showCategorySection = !showCategorySection },
            )
        }
        if (showCategorySection) {
            items(categoryStatuses, key = { it.category }) { status ->
                CategoryBudgetRow(status, viewModel)
            }
        }
    }
}

@Composable
private fun BudgetSectionButton(title: String, expanded: Boolean, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(title, modifier = Modifier.weight(1f))
            Icon(
                imageVector = if (expanded) Icons.Outlined.KeyboardArrowUp else Icons.Outlined.KeyboardArrowDown,
                contentDescription = if (expanded) "Collapse" else "Expand",
            )
        }
    }
}

@Composable
private fun BudgetOverview(report: BudgetReport) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Base income", money(report.baseMonthlyIncome), Modifier.weight(1f))
            MetricCard("Fixed costs", money(report.fixedCosts), Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Daily savings", money(report.dailySavingsGoal), Modifier.weight(1f))
            MetricCard("Flexible budget", money(report.netMonthlyFlexibleBudget), Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Adjusted target", money(report.adjustedDailyTarget), Modifier.weight(1f))
            MetricCard("Remaining", money(report.remainingFlexibleBudget), Modifier.weight(1f))
        }
    }
}

@Composable
private fun BudgetDepletionChart(report: BudgetReport) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Budget Depletion", style = MaterialTheme.typography.titleLarge)
            if (report.days.isEmpty()) {
                Text("No daily data for this month yet.")
            } else {
                Canvas(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(220.dp),
                ) {
                    val values = report.days.map { it.cumulativeFlexibleBalance } + report.netMonthlyFlexibleBudget + 0.0
                    val minValue = min(0.0, values.minOrNull() ?: 0.0)
                    val maxValue = max(0.0, values.maxOrNull() ?: 1.0)
                    val range = (maxValue - minValue).takeIf { it > 0.0 } ?: 1.0
                    val left = 18f
                    val right = size.width - 18f
                    val top = 18f
                    val bottom = size.height - 18f
                    fun x(index: Int): Float =
                        if (report.days.size <= 1) (left + right) / 2f else left + (index.toFloat() / (report.days.size - 1)) * (right - left)
                    fun y(value: Double): Float =
                        top + ((maxValue - value) / range).toFloat() * (bottom - top)

                    val zeroY = y(0.0)
                    drawLine(Color(0xFF9CA3AF), Offset(left, zeroY), Offset(right, zeroY), strokeWidth = 2f)
                    report.days.indices.drop(1).forEach { index ->
                        drawLine(
                            color = Color(0xFF2563EB),
                            start = Offset(x(index - 1), y(report.days[index - 1].cumulativeFlexibleBalance)),
                            end = Offset(x(index), y(report.days[index].cumulativeFlexibleBalance)),
                            strokeWidth = 4f,
                        )
                    }
                    report.days.forEachIndexed { index, day ->
                        drawCircle(
                            color = if (day.cumulativeFlexibleBalance >= 0.0) Color(0xFF16A34A) else Color(0xFFDC2626),
                            radius = 5f,
                            center = Offset(x(index), y(day.cumulativeFlexibleBalance)),
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun BalanceEditor(balances: com.peterle95.financetracker.domain.AssetBalances, viewModel: FinanceViewModel) {
    var bank by remember { mutableStateOf(balances.bankAccount.toFieldText()) }
    var wallet by remember { mutableStateOf(balances.wallet.toFieldText()) }
    var savings by remember { mutableStateOf(balances.savings.toFieldText()) }
    var investments by remember { mutableStateOf(balances.investments.toFieldText()) }
    var moneyLent by remember { mutableStateOf(balances.moneyLent.toFieldText()) }

    LaunchedEffect(balances) {
        bank = balances.bankAccount.toFieldText()
        wallet = balances.wallet.toFieldText()
        savings = balances.savings.toFieldText()
        investments = balances.investments.toFieldText()
        moneyLent = balances.moneyLent.toFieldText()
    }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Balances", style = MaterialTheme.typography.titleLarge)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MoneyField("Bank", bank, { bank = it }, Modifier.weight(1f))
                MoneyField("Wallet", wallet, { wallet = it }, Modifier.weight(1f))
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MoneyField("Savings", savings, { savings = it }, Modifier.weight(1f))
                MoneyField("Investments", investments, { investments = it }, Modifier.weight(1f))
            }
            MoneyField("Money Lent", moneyLent, { moneyLent = it })
            Button(
                onClick = { viewModel.updateBalances(bank, wallet, savings, investments, moneyLent) },
                modifier = Modifier.fillMaxWidth(),
            ) {
                Text("Save Balances")
            }
        }
    }
}

@Composable
private fun DailySavingsEditor(value: Double, viewModel: FinanceViewModel) {
    var amount by remember { mutableStateOf(value.toFieldText()) }
    LaunchedEffect(value) {
        amount = value.toFieldText()
    }
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            MoneyField("Daily Savings Goal", amount, { amount = it }, Modifier.weight(1f))
            Button(onClick = { viewModel.setDailySavingsGoal(amount) }) {
                Text("Save")
            }
        }
    }
}

@Composable
private fun IncomeSourceEditor(viewModel: FinanceViewModel) {
    var description by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var startDate by remember { mutableStateOf(todayIsoDate()) }
    var endDate by remember { mutableStateOf("") }
    EntryEditorCard(
        title = "Add Income Source",
        description = description,
        onDescriptionChange = { description = it },
        amount = amount,
        onAmountChange = { amount = it },
        startDate = startDate,
        onStartDateChange = { startDate = it },
        endDate = endDate,
        onEndDateChange = { endDate = it },
        actionLabel = "Add Income",
        onAction = {
            viewModel.addIncomeSource(amount, description, startDate, endDate)
            description = ""
            amount = ""
            endDate = ""
        },
    )
}

@Composable
private fun FixedCostEditor(viewModel: FinanceViewModel) {
    var description by remember { mutableStateOf("") }
    var amount by remember { mutableStateOf("") }
    var startDate by remember { mutableStateOf(todayIsoDate()) }
    var endDate by remember { mutableStateOf("") }
    EntryEditorCard(
        title = "Add Fixed Cost",
        description = description,
        onDescriptionChange = { description = it },
        amount = amount,
        onAmountChange = { amount = it },
        startDate = startDate,
        onStartDateChange = { startDate = it },
        endDate = endDate,
        onEndDateChange = { endDate = it },
        actionLabel = "Add Cost",
        onAction = {
            viewModel.addFixedCost(amount, description, startDate, endDate)
            description = ""
            amount = ""
            endDate = ""
        },
    )
}

@Composable
private fun IncomeSourceRow(source: IncomeSource, viewModel: FinanceViewModel) {
    EditableRecurringRow(
        title = source.description,
        amountValue = source.amount,
        startDateValue = source.startDate,
        endDateValue = source.endDate.orEmpty(),
        onSave = { amount, description, start, end ->
            viewModel.updateIncomeSource(source.key, amount, description, start, end)
        },
        onArchive = { viewModel.archiveIncomeSource(source.key) },
        onDelete = { viewModel.deleteIncomeSource(source.key) },
    )
}

@Composable
private fun FixedCostRow(cost: FixedCost, viewModel: FinanceViewModel) {
    EditableRecurringRow(
        title = cost.description,
        amountValue = cost.amount,
        startDateValue = cost.startDate,
        endDateValue = cost.endDate.orEmpty(),
        onSave = { amount, description, start, end ->
            viewModel.updateFixedCost(cost.key, amount, description, start, end)
        },
        onArchive = { viewModel.archiveFixedCost(cost.key) },
        onDelete = { viewModel.deleteFixedCost(cost.key) },
    )
}

@Composable
private fun EditableRecurringRow(
    title: String,
    amountValue: Double,
    startDateValue: String,
    endDateValue: String,
    onSave: (amount: String, description: String, startDate: String, endDate: String) -> Unit,
    onArchive: () -> Unit,
    onDelete: () -> Unit,
) {
    var description by remember(title) { mutableStateOf(title) }
    var amount by remember(amountValue) { mutableStateOf(amountValue.toFieldText()) }
    var startDate by remember(startDateValue) { mutableStateOf(startDateValue) }
    var endDate by remember(endDateValue) { mutableStateOf(endDateValue) }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Description") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MoneyField("Amount", amount, { amount = it }, Modifier.weight(1f))
                OutlinedTextField(
                    value = startDate,
                    onValueChange = { startDate = it },
                    label = { Text("Start") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                )
            }
            OutlinedTextField(
                value = endDate,
                onValueChange = { endDate = it },
                label = { Text("End (optional)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { onSave(amount, description, startDate, endDate) }) {
                    Text("Save")
                }
                OutlinedButton(onClick = onArchive) {
                    Text("Archive")
                }
                IconButton(onClick = onDelete) {
                    Icon(Icons.Outlined.Delete, contentDescription = "Delete")
                }
            }
        }
    }
}

@Composable
private fun EntryEditorCard(
    title: String,
    description: String,
    onDescriptionChange: (String) -> Unit,
    amount: String,
    onAmountChange: (String) -> Unit,
    startDate: String,
    onStartDateChange: (String) -> Unit,
    endDate: String,
    onEndDateChange: (String) -> Unit,
    actionLabel: String,
    onAction: () -> Unit,
) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            OutlinedTextField(
                value = description,
                onValueChange = onDescriptionChange,
                label = { Text("Description") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                MoneyField("Amount", amount, onAmountChange, Modifier.weight(1f))
                OutlinedTextField(
                    value = startDate,
                    onValueChange = onStartDateChange,
                    label = { Text("Start") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                )
            }
            OutlinedTextField(
                value = endDate,
                onValueChange = onEndDateChange,
                label = { Text("End (optional)") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Button(onClick = onAction, modifier = Modifier.fillMaxWidth()) {
                Text(actionLabel)
            }
        }
    }
}

@Composable
private fun CategoryBudgetRow(status: CategoryBudgetStatus, viewModel: FinanceViewModel) {
    var percent by remember(status.category) { mutableStateOf(status.percentLimit.toFieldText()) }
    LaunchedEffect(status.percentLimit) {
        percent = status.percentLimit.toFieldText()
    }
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(12.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text(status.category, style = MaterialTheme.typography.titleMedium)
                Text(
                    if (status.remaining >= 0.0) "${money(status.remaining)} left" else "${money(-status.remaining)} over",
                    color = if (status.remaining >= 0.0) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error,
                )
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                OutlinedTextField(
                    value = percent,
                    onValueChange = { percent = it },
                    label = { Text("Percent") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                )
                Button(onClick = { viewModel.setCategoryBudget(status.category, percent) }) {
                    Text("Save")
                }
            }
            Text(
                "Limit ${money(status.euroLimit)} · Spent ${money(status.spent)}",
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}

@Composable
private fun MoneyField(
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

private fun Double.toFieldText(): String =
    if (this == 0.0) "0" else "%.2f".format(this)
