package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.domain.todayIsoDate
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.CategoryDropdown

@Composable
fun AddTransactionScreen(viewModel: FinanceViewModel) {
    val categories by viewModel.categories.collectAsState()
    val syncStatus by viewModel.syncStatus.collectAsState()
    var type by remember { mutableStateOf(TransactionType.Expense) }
    var amount by remember { mutableStateOf("") }
    var category by remember { mutableStateOf(categories.forType(type).firstOrNull().orEmpty()) }
    var description by remember { mutableStateOf("") }
    var date by remember { mutableStateOf(todayIsoDate()) }
    var isBnpl by remember { mutableStateOf(true) }
    val currentCategories = categories.forType(type)

    LaunchedEffect(type, categories) {
        if (category !in currentCategories) category = currentCategories.firstOrNull().orEmpty()
    }

    LaunchedEffect(type) {
        isBnpl = type == TransactionType.Expense
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Text("Add Transaction", style = MaterialTheme.typography.headlineMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TransactionType.entries.forEach { item ->
                FilterChip(
                    selected = type == item,
                    onClick = { type = item },
                    label = { Text(item.label) },
                )
            }
        }
        OutlinedTextField(
            value = amount,
            onValueChange = { amount = it },
            label = { Text("Amount") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        CategoryDropdown(
            label = "Category",
            selected = category,
            categories = currentCategories,
            onSelected = { category = it },
        )
        OutlinedTextField(
            value = description,
            onValueChange = { description = it },
            label = { Text("Description") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = date,
            onValueChange = { date = it },
            label = { Text("Date") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        if (type == TransactionType.Expense) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Checkbox(
                    checked = isBnpl,
                    onCheckedChange = { isBnpl = it },
                )
                Text("BNPL / Pay next month", style = MaterialTheme.typography.labelLarge)
            }
            Text(
                "Books this expense on the 1st of next month while keeping the original spending date.",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
        Button(
            onClick = {
                viewModel.addTransaction(type, amount, category, description, date, isBnpl)
                amount = ""
                description = ""
                isBnpl = type == TransactionType.Expense
            },
            enabled = syncStatus.isConnected,
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Save")
        }
        if (!syncStatus.isConnected) {
            Text("Connect finance_data.json in Settings before adding transactions.")
        }
    }
}
