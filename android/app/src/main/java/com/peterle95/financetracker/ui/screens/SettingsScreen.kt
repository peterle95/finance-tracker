package com.peterle95.financetracker.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.material3.Button
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
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.ui.FinanceViewModel

@Composable
fun SettingsScreen(viewModel: FinanceViewModel) {
    val categories by viewModel.categories.collectAsState()
    val syncStatus by viewModel.syncStatus.collectAsState()
    var type by remember { mutableStateOf(TransactionType.Expense) }
    var newCategory by remember { mutableStateOf("") }
    val current = categories.forType(type)
    val connectLauncher = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        uri?.let(viewModel::connectSyncedFile)
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Settings", style = MaterialTheme.typography.headlineMedium)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            TransactionType.entries.forEach { item ->
                FilterChip(
                    selected = type == item,
                    onClick = { type = item },
                    label = { Text(item.label) },
                )
            }
        }
        Button(
            onClick = { connectLauncher.launch(arrayOf("application/json", "text/*", "*/*")) },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Connect synced finance_data.json")
        }
        Button(
            onClick = { viewModel.reloadFromSyncedFile() },
            modifier = Modifier.fillMaxWidth(),
        ) {
            Text("Reload from synced file")
        }
        Card {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(12.dp),
                verticalArrangement = Arrangement.spacedBy(4.dp),
            ) {
                Text("Synced file", style = MaterialTheme.typography.titleMedium)
                Text("File: ${syncStatus.fileName ?: "Not connected"}")
                Text("Last loaded: ${syncStatus.lastLoadedAt ?: "Never"}")
                Text("Last write: ${syncStatus.lastWrittenAt ?: "Never"}")
                syncStatus.lastError?.let { Text("Last error: $it", color = MaterialTheme.colorScheme.error) }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            OutlinedTextField(
                value = newCategory,
                onValueChange = { newCategory = it },
                label = { Text("New category") },
                singleLine = true,
                modifier = Modifier.weight(1f),
            )
            Button(
                onClick = {
                    val value = newCategory.trim()
                    if (value.isNotEmpty()) {
                        viewModel.setCategories(type, current + value)
                        newCategory = ""
                    }
                },
            ) {
                Text("Add")
            }
        }
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(current, key = { it }) { category ->
                Card {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                    ) {
                        Text(category, modifier = Modifier.weight(1f))
                        IconButton(onClick = { viewModel.setCategories(type, current - category) }) {
                            Icon(Icons.Outlined.Delete, contentDescription = "Delete")
                        }
                    }
                }
            }
        }
    }
}
