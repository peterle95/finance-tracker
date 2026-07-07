package com.peterle95.financetracker.ui.screens

import android.content.Intent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
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
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.SavingsGoal
import com.peterle95.financetracker.domain.SavingsGoals
import com.peterle95.financetracker.domain.SavingsGoalsSummary
import com.peterle95.financetracker.domain.formatAmountField
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.MetricCard
import com.peterle95.financetracker.ui.components.money

@Composable
fun SavingsGoalsScreen(viewModel: FinanceViewModel) {
    val settings by viewModel.budgetSettingsModel.collectAsState()
    val context = LocalContext.current
    val goals = remember(settings.savingsGoals) { SavingsGoals.sortedGoals(settings.savingsGoals) }
    val summary = remember(settings) { SavingsGoals.summary(settings) }
    var selectedGoalKey by rememberSaveable { mutableStateOf<String?>(null) }
    var allocationGoalKey by rememberSaveable { mutableStateOf<String?>(null) }
    var reportText by rememberSaveable { mutableStateOf("") }
    val selectedGoal = settings.savingsGoals.firstOrNull { it.key == selectedGoalKey }
    val allocationGoal = settings.savingsGoals.firstOrNull { it.key == allocationGoalKey }

    LaunchedEffect(settings.savingsGoals, selectedGoalKey, allocationGoalKey) {
        if (selectedGoalKey != null && selectedGoal == null) selectedGoalKey = null
        if (allocationGoalKey != null && allocationGoal == null) allocationGoalKey = null
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text("Savings Goals", style = MaterialTheme.typography.headlineMedium)
        }
        item {
            SavingsOverview(summary)
        }
        item {
            GoalActions(
                hasReport = reportText.isNotBlank(),
                onAutoDistribute = { viewModel.autoDistributeSavings() },
                onGenerateReport = { reportText = SavingsGoals.reportText(settings) },
                onShareReport = {
                    val text = reportText.ifBlank { SavingsGoals.reportText(settings) }
                    val intent = Intent(Intent.ACTION_SEND).apply {
                        type = "text/plain"
                        putExtra(Intent.EXTRA_SUBJECT, "Savings Goals Report")
                        putExtra(Intent.EXTRA_TEXT, text)
                    }
                    context.startActivity(Intent.createChooser(intent, "Share Savings Goals Report"))
                },
            )
        }
        if (allocationGoal != null) {
            item {
                AllocationEditor(
                    goal = allocationGoal,
                    summary = summary,
                    available = SavingsGoals.availableForGoal(settings, allocationGoal.key),
                    onSave = { amount ->
                        viewModel.allocateSavingsGoal(allocationGoal.key, amount)
                        allocationGoalKey = null
                    },
                    onCancel = { allocationGoalKey = null },
                )
            }
        }
        item {
            GoalEditor(
                selectedGoal = selectedGoal,
                onAdd = { name, description, targetAmount, priority, targetDate ->
                    viewModel.addSavingsGoal(name, description, targetAmount, priority, targetDate)
                },
                onUpdate = { key, name, description, targetAmount, priority, targetDate ->
                    viewModel.updateSavingsGoal(key, name, description, targetAmount, priority, targetDate)
                    selectedGoalKey = null
                },
                onClear = { selectedGoalKey = null },
            )
        }
        if (goals.isEmpty()) {
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        "No goals yet. Create your first goal.",
                        modifier = Modifier.padding(16.dp),
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        } else {
            items(goals, key = { it.key }) { goal ->
                SavingsGoalCard(
                    goal = goal,
                    selected = goal.key == selectedGoalKey,
                    onEdit = { selectedGoalKey = goal.key },
                    onAllocate = { allocationGoalKey = goal.key },
                    onDelete = { viewModel.deleteSavingsGoal(goal.key) },
                    onArchive = { viewModel.deleteSavingsGoal(goal.key) },
                )
            }
        }
        if (reportText.isNotBlank()) {
            item {
                Card(modifier = Modifier.fillMaxWidth()) {
                    Text(
                        text = reportText,
                        style = MaterialTheme.typography.bodySmall,
                        fontFamily = FontFamily.Monospace,
                        modifier = Modifier
                            .fillMaxWidth()
                            .horizontalScroll(rememberScrollState())
                            .padding(12.dp),
                    )
                }
            }
        }
    }
}

@Composable
private fun SavingsOverview(summary: SavingsGoalsSummary) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Savings", money(summary.totalSavings), Modifier.weight(1f))
            MetricCard("Allocated", money(summary.totalAllocated), Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Unallocated", money(summary.unallocated), Modifier.weight(1f))
            MetricCard("Progress", "%.1f%%".format(summary.overallProgress), Modifier.weight(1f))
        }
        Text(
            "Goals: ${summary.totalGoals} | Active: ${summary.activeGoals} | Completed: ${summary.completedGoals}",
            style = MaterialTheme.typography.labelLarge,
        )
    }
}

@Composable
private fun GoalActions(
    hasReport: Boolean,
    onAutoDistribute: () -> Unit,
    onGenerateReport: () -> Unit,
    onShareReport: () -> Unit,
) {
    ActionRow {
        Button(onClick = onAutoDistribute) {
            Text("Auto-Distribute")
        }
        OutlinedButton(onClick = onGenerateReport) {
            Text("Generate Report")
        }
        OutlinedButton(onClick = onShareReport) {
            Text(if (hasReport) "Share Report" else "Share")
        }
    }
}

@Composable
private fun GoalEditor(
    selectedGoal: SavingsGoal?,
    onAdd: (String, String, String, String, String) -> Unit,
    onUpdate: (String, String, String, String, String, String) -> Unit,
    onClear: () -> Unit,
) {
    var name by rememberSaveable { mutableStateOf("") }
    var description by rememberSaveable { mutableStateOf("") }
    var targetAmount by rememberSaveable { mutableStateOf("") }
    var priority by rememberSaveable { mutableStateOf("Medium") }
    var targetDate by rememberSaveable { mutableStateOf("") }

    LaunchedEffect(selectedGoal?.key) {
        if (selectedGoal != null) {
            name = selectedGoal.name
            description = selectedGoal.description
            targetAmount = selectedGoal.targetAmount.toFieldText()
            priority = selectedGoal.priority
            targetDate = selectedGoal.targetDate.orEmpty()
        } else {
            name = ""
            description = ""
            targetAmount = ""
            priority = "Medium"
            targetDate = ""
        }
    }

    fun clear() {
        name = ""
        description = ""
        targetAmount = ""
        priority = "Medium"
        targetDate = ""
        onClear()
    }

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
        ) {
            Text(if (selectedGoal == null) "Add Goal" else "Edit Goal", style = MaterialTheme.typography.titleLarge)
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Goal Name") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            OutlinedTextField(
                value = description,
                onValueChange = { description = it },
                label = { Text("Description") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = targetAmount,
                    onValueChange = { targetAmount = it },
                    label = { Text("Target Amount") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                )
                OutlinedTextField(
                    value = targetDate,
                    onValueChange = { targetDate = it },
                    label = { Text("Target Date") },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                )
            }
            Text("Priority", style = MaterialTheme.typography.labelLarge)
            ActionRow {
                listOf("High", "Medium", "Low").forEach { item ->
                    FilterChip(
                        selected = priority == item,
                        onClick = { priority = item },
                        label = { Text(item) },
                    )
                }
            }
            ActionRow {
                Button(
                    onClick = {
                        if (selectedGoal == null) {
                            onAdd(name, description, targetAmount, priority, targetDate)
                        } else {
                            onUpdate(selectedGoal.key, name, description, targetAmount, priority, targetDate)
                        }
                        clear()
                    },
                ) {
                    Text(if (selectedGoal == null) "Add Goal" else "Update Selected")
                }
                OutlinedButton(onClick = { clear() }) {
                    Text("Clear Form")
                }
            }
        }
    }
}

@Composable
private fun AllocationEditor(
    goal: SavingsGoal,
    summary: SavingsGoalsSummary,
    available: Double,
    onSave: (String) -> Unit,
    onCancel: () -> Unit,
) {
    var amount by rememberSaveable(goal.key) { mutableStateOf(goal.allocatedAmount.toFieldText()) }
    val progress = SavingsGoals.progress(goal)

    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Text("Allocate Savings", style = MaterialTheme.typography.titleLarge)
            Text(goal.name, style = MaterialTheme.typography.titleMedium)
            Text("Target: ${money(goal.targetAmount)}")
            Text("Currently Allocated: ${money(goal.allocatedAmount)}")
            Text("Still Needed: ${money(progress.remaining)}")
            Text("Total Savings: ${money(summary.totalSavings)}")
            Text("Available for this goal: ${money(available)}")
            OutlinedTextField(
                value = amount,
                onValueChange = { amount = it },
                label = { Text("New Total Allocation") },
                singleLine = true,
                modifier = Modifier.fillMaxWidth(),
            )
            ActionRow {
                OutlinedButton(onClick = { amount = available.toFieldText() }) {
                    Text("Max Available")
                }
                OutlinedButton(onClick = { amount = goal.targetAmount.toFieldText() }) {
                    Text("Complete Goal")
                }
                OutlinedButton(onClick = { amount = 0.0.toFieldText() }) {
                    Text("Clear")
                }
            }
            ActionRow {
                Button(onClick = { onSave(amount) }) {
                    Text("Save")
                }
                OutlinedButton(onClick = onCancel) {
                    Text("Cancel")
                }
            }
        }
    }
}

@Composable
private fun SavingsGoalCard(
    goal: SavingsGoal,
    selected: Boolean,
    onEdit: () -> Unit,
    onAllocate: () -> Unit,
    onDelete: () -> Unit,
    onArchive: () -> Unit,
) {
    val progress = SavingsGoals.progress(goal)
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onEdit),
        colors = CardDefaults.cardColors(
            containerColor = if (selected) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            },
        ),
    ) {
        Column(
            modifier = Modifier.padding(14.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Row(horizontalArrangement = Arrangement.SpaceBetween, modifier = Modifier.fillMaxWidth()) {
                Text(goal.name, style = MaterialTheme.typography.titleLarge, modifier = Modifier.weight(1f))
                Text(goal.priority, style = MaterialTheme.typography.labelLarge)
            }
            if (goal.description.isNotBlank()) {
                Text(goal.description, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Text("${money(goal.allocatedAmount)} / ${money(goal.targetAmount)}")
            LinearProgressIndicator(
                progress = { (progress.progressPercent / 100.0).coerceIn(0.0, 1.0).toFloat() },
                modifier = Modifier.fillMaxWidth(),
            )
            Text(
                "${"%.1f".format(progress.progressPercent)}% | ${money(progress.remaining)} remaining",
                style = MaterialTheme.typography.bodySmall,
            )
            goal.targetDate?.let {
                Text("Target Date: $it", style = MaterialTheme.typography.bodySmall)
            }
            if (progress.isComplete) {
                Text("Goal Achieved", color = MaterialTheme.colorScheme.primary)
                goal.completionDate?.let {
                    Text("Completed: $it", style = MaterialTheme.typography.bodySmall)
                }
            }
            ActionRow {
                OutlinedButton(onClick = onEdit) {
                    Text("Edit")
                }
                Button(onClick = onAllocate) {
                    Text("Allocate Savings")
                }
                IconButton(onClick = onDelete) {
                    Icon(Icons.Outlined.Delete, contentDescription = "Delete goal")
                }
                if (progress.isComplete) {
                    OutlinedButton(onClick = onArchive) {
                        Text("Archive")
                    }
                }
            }
        }
    }
}

@Composable
private fun ActionRow(content: @Composable RowScope.() -> Unit) {
    Row(
        modifier = Modifier.horizontalScroll(rememberScrollState()),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalAlignment = Alignment.CenterVertically,
        content = content,
    )
}

private fun Double.toFieldText(): String =
    formatAmountField(this)
