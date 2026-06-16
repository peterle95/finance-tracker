package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.ui.FinanceViewModel

@Composable
fun InsightsScreen(viewModel: FinanceViewModel) {
    val summary by viewModel.insightsJson.collectAsState()
    val vertical = rememberScrollState()
    val horizontal = rememberScrollState()

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
    ) {
        Text("Insights", style = MaterialTheme.typography.headlineMedium)
        Text(
            text = summary,
            modifier = Modifier
                .weight(1f)
                .verticalScroll(vertical)
                .horizontalScroll(horizontal)
                .padding(top = 12.dp),
            fontFamily = FontFamily.Monospace,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}
