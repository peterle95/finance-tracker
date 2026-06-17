package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
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

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Transactions", style = MaterialTheme.typography.headlineMedium)
        CategoryDropdown(
            label = "Month",
            selected = monthLabels[selectedMonthKey] ?: TransactionUiLogic.monthLabel(TransactionUiLogic.ALL_MONTHS_KEY),
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
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(filtered, key = { it.uiKey }) { transaction ->
                TransactionRow(transaction = transaction, onDelete = { viewModel.deleteTransaction(transaction.exportId) })
            }
        }
    }
}

@Composable
private fun TransactionRow(transaction: FinanceTransaction, onDelete: () -> Unit) {
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
            Column {
                Text(money(transaction.amount), style = MaterialTheme.typography.labelLarge)
                IconButton(onClick = onDelete) {
                    Icon(Icons.Outlined.Delete, contentDescription = "Delete")
                }
            }
        }
    }
}
