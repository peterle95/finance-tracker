package com.peterle95.financetracker.ui.screens

import android.content.Intent
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
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
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.ProjectionMode
import com.peterle95.financetracker.domain.ProjectionService
import com.peterle95.financetracker.ui.FinanceViewModel

@Composable
fun ProjectionScreen(viewModel: FinanceViewModel) {
    val settings by viewModel.budgetSettingsModel.collectAsState()
    val context = LocalContext.current

    var numMonths by remember { mutableStateOf("12") }
    var mode by remember { mutableStateOf(ProjectionMode.TargetSavings) }
    var historyMonths by remember { mutableStateOf("6") }
    var reportText by remember { mutableStateOf("") }
    var errorMessage by remember { mutableStateOf<String?>(null) }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Projection", style = MaterialTheme.typography.headlineMedium)

        OutlinedTextField(
            value = numMonths,
            onValueChange = { numMonths = it; errorMessage = null },
            label = { Text("Number of months to project") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )

        Text("Projection mode", style = MaterialTheme.typography.labelLarge)
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            ProjectionMode.entries.forEach { item ->
                FilterChip(
                    selected = mode == item,
                    onClick = { mode = item; errorMessage = null },
                    label = {
                        Text(
                            when (item) {
                                ProjectionMode.TargetSavings -> "Target savings"
                                ProjectionMode.NetWorthTrend -> "Net worth trend"
                            },
                        )
                    },
                )
            }
        }

        OutlinedTextField(
            value = historyMonths,
            onValueChange = { historyMonths = it; errorMessage = null },
            label = { Text("Months to analyze") },
            singleLine = true,
            enabled = mode == ProjectionMode.NetWorthTrend,
            modifier = Modifier.fillMaxWidth(),
        )

        if (errorMessage != null) {
            Text(errorMessage!!, color = MaterialTheme.colorScheme.error)
        }

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = {
                    val months = numMonths.toIntOrNull()
                    if (months == null || months <= 0) {
                        errorMessage = "Number of months must be a positive integer."
                        return@Button
                    }
                    val hist = historyMonths.toIntOrNull()
                    if (mode == ProjectionMode.NetWorthTrend && (hist == null || hist <= 0)) {
                        errorMessage = "Months to analyze must be a positive integer."
                        return@Button
                    }
                    errorMessage = null
                    reportText = ProjectionService.projectionText(
                        budgetSettings = settings,
                        numMonths = months,
                        mode = mode,
                        historyMonths = hist ?: 6,
                    )
                },
            ) {
                Text("Generate Projection")
            }
            if (reportText.isNotBlank()) {
                OutlinedButton(
                    onClick = {
                        val intent = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_SUBJECT, "Financial Projection")
                            putExtra(Intent.EXTRA_TEXT, reportText)
                        }
                        context.startActivity(Intent.createChooser(intent, "Share Projection"))
                    },
                ) {
                    Text("Share Projection")
                }
            }
        }

        if (reportText.isNotBlank()) {
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
