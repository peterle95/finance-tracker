package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.MetricCard
import com.peterle95.financetracker.ui.components.money

@Composable
fun DashboardScreen(viewModel: FinanceViewModel) {
    val dashboard by viewModel.dashboard.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text("Dashboard", style = MaterialTheme.typography.headlineMedium)
            Text(dashboard.currentMonth, style = MaterialTheme.typography.titleMedium)
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
                    MetricCard("Balance", money(it), Modifier.weight(1f))
                }
            }
        }
        item {
            Text("Top Expense Categories", style = MaterialTheme.typography.titleLarge)
            HorizontalDivider(Modifier.padding(top = 8.dp))
        }
        if (dashboard.topExpenseCategories.isEmpty()) {
            item { Text("No expenses for this month yet.") }
        } else {
            items(dashboard.topExpenseCategories) { (category, total) ->
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(category)
                    Text(money(total), style = MaterialTheme.typography.labelLarge)
                }
            }
        }
    }
}
