package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionUiLogic
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.CategoryDropdown
import com.peterle95.financetracker.ui.components.money
import java.time.YearMonth

@Composable
fun TransactionsScreen(viewModel: FinanceViewModel) {
    val rows by viewModel.transactions.collectAsState()
    val categories by viewModel.categories.collectAsState()
    val currentMonth = remember { YearMonth.now() }
    var selectedMonthKey by remember { mutableStateOf(currentMonth.toString()) }
    var typeFilter by remember { mutableStateOf<TransactionType?>(null) }
    var categoryFilter by remember { mutableStateOf("") }
    var search by remember { mutableStateOf("") }
    var editingTransaction by remember { mutableStateOf<FinanceTransaction?>(null) }
    val monthOptions = listOf(TransactionUiLogic.ALL_MONTHS_KEY) +
        TransactionUiLogic.availableMonthKeys(rows, currentMonth)
    val monthLabels = monthOptions.associateWith { TransactionUiLogic.monthLabel(it) }
    val monthLabelToKey = monthLabels.entries.associate { (key, label) -> label to key }
    val categoryOptions = listOf("All") + TransactionType.entries.flatMap { categories.forType(it) }.distinct().sorted()

    val filtered = TransactionUiLogic.filterTransactions(
        transactions = rows,
        selectedMonthKey = selectedMonthKey,
        categoryFilter = categoryFilter,
        typeFilter = typeFilter,
        searchText = search,
    )

    editingTransaction?.let { transaction ->
        EditTransactionDialog(
            transaction = transaction,
            categories = categories,
            onDismiss = { editingTransaction = null },
            onSave = { type, amount, category, description, date, behaviorDate ->
                viewModel.updateTransaction(
                    exportId = transaction.exportId,
                    type = type,
                    amountText = amount,
                    category = category,
                    description = description,
                    date = date,
                    behaviorDate = behaviorDate.ifBlank { null },
                )
                editingTransaction = null
            },
        )
    }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp),
    ) {
        item {
            Column(
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
                Text("Transactions", style = MaterialTheme.typography.headlineMedium)
                CategoryDropdown(
                    label = "Month",
                    selected = monthLabels[selectedMonthKey]
                        ?: TransactionUiLogic.monthLabel(TransactionUiLogic.ALL_MONTHS_KEY),
                    categories = monthOptions.map { monthLabels.getValue(it) },
                    onSelected = { selectedMonthKey = monthLabelToKey.getValue(it) },
                )
                CategoryDropdown(
                    label = "Category",
                    selected = categoryFilter.ifBlank { "All" },
                    categories = categoryOptions,
                    onSelected = { categoryFilter = it },
                )
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(selected = typeFilter == null, onClick = { typeFilter = null }, label = { Text("All") })
                    TransactionType.entries.forEach { item ->
                        FilterChip(
                            selected = typeFilter == item,
                            onClick = { typeFilter = item },
                            label = { Text(item.label) },
                        )
                    }
                }
                OutlinedTextField(
                    value = search,
                    onValueChange = { search = it },
                    label = { Text("Search description") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        }
        items(filtered, key = { it.uiKey }) { transaction ->
            TransactionRow(
                transaction = transaction,
                onDelete = { viewModel.deleteTransaction(transaction.exportId) },
                onModify = { editingTransaction = transaction },
            )
        }
    }
}

@Composable
private fun TransactionRow(
    transaction: FinanceTransaction,
    onDelete: () -> Unit,
    onModify: () -> Unit,
) {
    Card {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Column(Modifier.weight(1f)) {
                Text(transaction.description.ifBlank { transaction.category }, style = MaterialTheme.typography.titleMedium)
                val dateText = transaction.behaviorDate?.takeIf { it.isNotBlank() }?.let {
                    "Booked: ${transaction.date} \u00B7 Spent: $it"
                } ?: "${transaction.date} - ${transaction.type.label} - ${transaction.category}"
                Text(
                    dateText,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
                if (!transaction.behaviorDate.isNullOrBlank()) {
                    Text(
                        "${transaction.type.label} - ${transaction.category}",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                Text(money(transaction.amount), style = MaterialTheme.typography.labelLarge)
                OutlinedButton(onClick = onModify) {
                    Text("Modify")
                }
                IconButton(onClick = onDelete) {
                    Icon(Icons.Outlined.Delete, contentDescription = "Delete")
                }
            }
        }
    }
}

@Composable
private fun EditTransactionDialog(
    transaction: FinanceTransaction,
    categories: CategoryState,
    onDismiss: () -> Unit,
    onSave: (
        type: TransactionType,
        amount: String,
        category: String,
        description: String,
        date: String,
        behaviorDate: String,
    ) -> Unit,
) {
    var type by remember(transaction.uiKey) { mutableStateOf(transaction.type) }
    var amount by remember(transaction.uiKey) { mutableStateOf(transaction.amount.toString()) }
    var category by remember(transaction.uiKey) { mutableStateOf(transaction.category) }
    var description by remember(transaction.uiKey) { mutableStateOf(transaction.description) }
    var date by remember(transaction.uiKey) { mutableStateOf(transaction.date) }
    var behaviorDate by remember(transaction.uiKey) { mutableStateOf(transaction.behaviorDate.orEmpty()) }
    val currentCategories = categories.forType(type)

    LaunchedEffect(type, categories) {
        if (category !in currentCategories) {
            category = currentCategories.firstOrNull().orEmpty()
        }
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Edit Transaction") },
        text = {
            Column(
                modifier = Modifier.verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp),
            ) {
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
                OutlinedTextField(
                    value = behaviorDate,
                    onValueChange = { behaviorDate = it },
                    label = { Text("Behavior date (optional)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                )
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    onSave(type, amount, category, description, date, behaviorDate)
                },
            ) {
                Text("Update")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        },
    )
}
