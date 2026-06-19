package com.peterle95.financetracker.ui.screens

import android.content.Intent
import android.graphics.Paint
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
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.FilterChip
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.PathEffect
import androidx.compose.ui.graphics.drawscope.DrawScope
import androidx.compose.ui.graphics.nativeCanvas
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.AssetAllocation
import com.peterle95.financetracker.domain.AssetSnapshot
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.NetWorthMath
import com.peterle95.financetracker.domain.todayIsoDate
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.MetricCard
import com.peterle95.financetracker.ui.components.money
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

private enum class NetWorthChart(val label: String) {
    NetWorth("Net Worth"),
    Allocation("Allocation"),
    Breakdown("Breakdown"),
}

private val netWorthColors = listOf(
    Color(0xFF2563EB),
    Color(0xFF16A34A),
    Color(0xFFF59E0B),
    Color(0xFFDC2626),
    Color(0xFF7C3AED),
)

@Composable
fun NetWorthScreen(viewModel: FinanceViewModel) {
    val settings by viewModel.budgetSettingsModel.collectAsState()
    val summary = remember(settings) { NetWorthMath.buildSummary(settings) }
    val context = LocalContext.current
    var chart by remember { mutableStateOf(NetWorthChart.NetWorth) }
    var snapshotDate by remember { mutableStateOf(todayIsoDate()) }
    var snapshotNote by remember { mutableStateOf("") }
    var showReport by remember { mutableStateOf(false) }

    LazyColumn(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        item {
            Text("Net Worth", style = MaterialTheme.typography.headlineMedium)
        }
        item {
            MetricCard("Current Net Worth", money(summary.currentNetWorth), Modifier.fillMaxWidth())
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                listOf(1, 3).forEach { months ->
                    val change = summary.changes[months]
                    MetricCard(
                        "${months}M change",
                        change?.let { signedMoney(it.change) } ?: "No data",
                        Modifier.weight(1f),
                    )
                }
            }
        }
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                listOf(6, 12).forEach { months ->
                    val change = summary.changes[months]
                    MetricCard(
                        "${months}M change",
                        change?.let { "${signedMoney(it.change)} (${signedPercent(it.changePercent)})" } ?: "No data",
                        Modifier.weight(1f),
                    )
                }
            }
        }
        item { AssetBalanceCards(settings) }
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("Visualization", style = MaterialTheme.typography.titleLarge)
                    Row(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        NetWorthChart.entries.forEach { option ->
                            FilterChip(
                                selected = chart == option,
                                onClick = { chart = option },
                                label = { Text(option.label) },
                            )
                        }
                    }
                    when (chart) {
                        NetWorthChart.NetWorth -> NetWorthLineChart(settings)
                        NetWorthChart.Allocation -> AllocationChart(summary.allocation)
                        NetWorthChart.Breakdown -> AssetBreakdownChart(settings.assetSnapshots)
                    }
                }
            }
        }
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("Record Snapshot", style = MaterialTheme.typography.titleLarge)
                    OutlinedTextField(
                        value = snapshotDate,
                        onValueChange = { snapshotDate = it },
                        label = { Text("Date") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = snapshotNote,
                        onValueChange = { snapshotNote = it },
                        label = { Text("Note") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Button(
                        onClick = {
                            viewModel.recordAssetSnapshot(snapshotDate, snapshotNote)
                            snapshotNote = ""
                        },
                        modifier = Modifier.fillMaxWidth(),
                    ) {
                        Text("Record Snapshot")
                    }
                }
            }
        }
        item {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp),
                ) {
                    Text("Net Worth Report", style = MaterialTheme.typography.titleLarge)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { showReport = !showReport }) {
                            Text(if (showReport) "Hide Report" else "Show Report")
                        }
                        OutlinedButton(
                            onClick = {
                                val intent = Intent(Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(Intent.EXTRA_SUBJECT, "Net worth report")
                                    putExtra(Intent.EXTRA_TEXT, summary.reportText)
                                }
                                context.startActivity(Intent.createChooser(intent, "Share net worth report"))
                            },
                        ) {
                            Text("Share")
                        }
                    }
                    if (showReport) {
                        Text(
                            summary.reportText,
                            style = MaterialTheme.typography.bodySmall,
                            modifier = Modifier.horizontalScroll(rememberScrollState()),
                        )
                    }
                }
            }
        }
        item {
            Text("Snapshot History", style = MaterialTheme.typography.titleLarge)
        }
        items(summary.snapshots, key = { it.date }) { snapshot ->
            SnapshotRow(snapshot, onDelete = { viewModel.deleteAssetSnapshot(snapshot.date) })
        }
    }
}

@Composable
private fun AssetBalanceCards(settings: BudgetSettings) {
    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Bank", money(settings.balances.bankAccount), Modifier.weight(1f))
            MetricCard("Wallet", money(settings.balances.wallet), Modifier.weight(1f))
        }
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            MetricCard("Savings", money(settings.balances.savings), Modifier.weight(1f))
            MetricCard("Investments", money(settings.balances.investments), Modifier.weight(1f))
        }
        MetricCard("Money Lent", money(settings.balances.moneyLent), Modifier.fillMaxWidth())
    }
}

@Composable
private fun SnapshotRow(snapshot: AssetSnapshot, onDelete: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Column(Modifier.weight(1f)) {
                Text(snapshot.date, style = MaterialTheme.typography.titleMedium)
                Text(money(snapshot.netWorth), style = MaterialTheme.typography.labelLarge)
                if (snapshot.note.isNotBlank()) {
                    Text(snapshot.note, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
            IconButton(onClick = onDelete) {
                Icon(Icons.Outlined.Delete, contentDescription = "Delete snapshot")
            }
        }
    }
}

@Composable
private fun NetWorthLineChart(settings: BudgetSettings) {
    val points = settings.assetSnapshots.map { it.date to it.netWorth }
    if (points.isEmpty()) {
        Text("No snapshots recorded yet.")
        return
    }
    SimpleLineChart(
        labels = points.map { it.first },
        series = listOf("Net Worth" to points.map { it.second }),
    )
}

@Composable
private fun AllocationChart(allocation: List<AssetAllocation>) {
    if (allocation.isEmpty()) {
        Text("No positive assets to display.")
        return
    }
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(230.dp),
    ) {
        val total = allocation.sumOf { it.value }
        var startAngle = -90f
        val diameter = min(size.width, size.height) * 0.78f
        val topLeft = Offset((size.width - diameter) / 2f, (size.height - diameter) / 2f)
        allocation.forEachIndexed { index, item ->
            val sweep = (item.value / total * 360.0).toFloat()
            drawArc(
                color = netWorthColors[index % netWorthColors.size],
                startAngle = startAngle,
                sweepAngle = sweep,
                useCenter = true,
                topLeft = topLeft,
                size = androidx.compose.ui.geometry.Size(diameter, diameter),
            )
            startAngle += sweep
        }
    }
    Legend(allocation.map { it.label to "${money(it.value)} (${it.percent.toInt()}%)" })
}

@Composable
private fun AssetBreakdownChart(snapshots: List<AssetSnapshot>) {
    if (snapshots.size < 2) {
        Text("At least two snapshots are needed for an asset breakdown.")
        return
    }
    val series = listOf(
        "Bank" to snapshots.map { it.bankBalance },
        "Wallet" to snapshots.map { it.walletBalance },
        "Savings" to snapshots.map { it.savingsBalance },
        "Investments" to snapshots.map { it.investmentBalance },
        "Money Lent" to snapshots.map { it.moneyLentBalance },
    )
    SimpleLineChart(labels = snapshots.map { it.date }, series = series)
}

@Composable
private fun SimpleLineChart(labels: List<String>, series: List<Pair<String, List<Double>>>) {
    Canvas(
        modifier = Modifier
            .fillMaxWidth()
            .height(250.dp),
    ) {
        val values = series.flatMap { it.second } + 0.0
        val minValue = min(0.0, values.minOrNull() ?: 0.0)
        val maxValue = max(0.0, values.maxOrNull() ?: 1.0)
        val range = (maxValue - minValue).takeIf { it > 0.0 } ?: 1.0
        val left = 132f
        val right = size.width - 18f
        val top = 30f
        val bottom = size.height - 44f
        fun x(index: Int): Float =
            if (labels.size <= 1) (left + right) / 2f else left + (index.toFloat() / (labels.size - 1)) * (right - left)
        fun y(value: Double): Float =
            top + ((maxValue - value) / range).toFloat() * (bottom - top)

        val axisColor = Color(0xFF9CA3AF)
        val labelColor = Color(0xFF6B7280)
        val gridColor = axisColor.copy(alpha = 0.55f)
        val gridPathEffect = PathEffect.dashPathEffect(floatArrayOf(8f, 8f))
        val yTickCount = 5
        (0..yTickCount).forEach { tick ->
            val value = minValue + (range * tick / yTickCount)
            val tickY = y(value)
            drawLine(
                color = gridColor,
                start = Offset(left, tickY),
                end = Offset(right, tickY),
                strokeWidth = 1.5f,
                pathEffect = gridPathEffect,
            )
            drawAxisText(
                text = money(value),
                x = left - 10f,
                y = tickY + 7f,
                color = labelColor,
                textSize = 20f,
                align = Paint.Align.RIGHT,
            )
        }
        if (minValue < 0.0 && maxValue > 0.0) {
            val zeroY = y(0.0)
            drawLine(
                color = gridColor,
                start = Offset(left, zeroY),
                end = Offset(right, zeroY),
                strokeWidth = 1.5f,
                pathEffect = gridPathEffect,
            )
            drawAxisText(money(0.0), left - 10f, zeroY + 7f, labelColor, 20f, Paint.Align.RIGHT)
        }
        drawLine(axisColor, Offset(left, top), Offset(left, bottom), strokeWidth = 1.5f)
        drawLine(axisColor, Offset(left, bottom), Offset(right, bottom), strokeWidth = 1.5f)
        drawAxisText("Amount (EUR)", 4f, 16f, labelColor, 20f, Paint.Align.LEFT)
        drawAxisText("Time", right, size.height - 4f, labelColor, 20f, Paint.Align.RIGHT)

        val labelStep = (labels.size / 4).coerceAtLeast(1)
        labels.forEachIndexed { index, label ->
            if (labels.size <= 5 || index % labelStep == 0 || index == labels.lastIndex) {
                drawAxisText(timeAxisLabel(label), x(index), size.height - 22f, labelColor, 20f, Paint.Align.CENTER)
            }
        }

        series.forEachIndexed { seriesIndex, item ->
            val color = netWorthColors[seriesIndex % netWorthColors.size]
            item.second.indices.drop(1).forEach { index ->
                drawLine(
                    color = color,
                    start = Offset(x(index - 1), y(item.second[index - 1])),
                    end = Offset(x(index), y(item.second[index])),
                    strokeWidth = 4f,
                )
            }
            item.second.forEachIndexed { index, value ->
                drawCircle(color = color, radius = 5f, center = Offset(x(index), y(value)))
            }
        }
    }
    Legend(series.map { it.first to "" })
}

private fun DrawScope.drawAxisText(
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

private fun timeAxisLabel(label: String): String =
    if (label.length >= 10 && label[4] == '-' && label[7] == '-') label.substring(5, 10) else label

@Composable
private fun Legend(entries: List<Pair<String, String>>) {
    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
        entries.forEachIndexed { index, entry ->
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .background(netWorthColors[index % netWorthColors.size]),
                )
                Text(entry.first, modifier = Modifier.weight(1f))
                if (entry.second.isNotBlank()) Text(entry.second, style = MaterialTheme.typography.labelLarge)
            }
        }
    }
}

private fun signedMoney(value: Double): String =
    if (value >= 0.0) "+${money(value)}" else "-${money(abs(value))}"

private fun signedPercent(value: Double): String =
    if (value >= 0.0) "+%.1f%%".format(value) else "%.1f%%".format(value)
