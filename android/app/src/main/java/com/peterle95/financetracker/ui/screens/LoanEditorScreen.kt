package com.peterle95.financetracker.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.domain.formatAmountField
import com.peterle95.financetracker.domain.parseAmountText
import com.peterle95.financetracker.domain.todayIsoDate
import com.peterle95.financetracker.ui.FinanceViewModel
import com.peterle95.financetracker.ui.components.money
import java.time.LocalDate
import kotlin.math.abs

@Composable
fun LoanEditorScreen(
    viewModel: FinanceViewModel,
    loanKey: String,
    onDone: () -> Unit,
) {
    val settings by viewModel.budgetSettingsModel.collectAsState()
    val loan = settings.loans.firstOrNull { it.key == loanKey || it.id == loanKey }

    if (loan == null) {
        Text("Loan not found", modifier = Modifier.padding(16.dp))
        return
    }

    var borrower by remember(loan.key) { mutableStateOf(loan.borrower) }
    var amount by remember(loan.key) { mutableStateOf(formatAmountField(loan.amount)) }
    var description by remember(loan.key) { mutableStateOf(loan.description) }
    var notes by remember(loan.key) { mutableStateOf(loan.notes) }
    var date by remember(loan.key) { mutableStateOf(loan.date.ifBlank { todayIsoDate() }) }
    var error by remember(loan.key) { mutableStateOf<String?>(null) }
    var showAmountConfirmation by remember(loan.key) { mutableStateOf(false) }

    fun save() {
        val parsedAmount = parseAmountText(amount)
        error = when {
            borrower.trim().isBlank() -> "Borrower cannot be empty."
            parsedAmount == null -> "Amount must be a number."
            parsedAmount == 0.0 -> "Amount cannot be zero."
            runCatching { LocalDate.parse(date) }.isFailure -> "Date must use YYYY-MM-DD."
            else -> null
        }
        if (error != null || parsedAmount == null) {
            return
        }
        showAmountConfirmation = abs(parsedAmount - loan.amount) > 0.000001
        if (!showAmountConfirmation) {
            viewModel.updateLoan(loan.key, borrower, amount, description, date, notes)
            onDone()
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("Modify loan", style = androidx.compose.material3.MaterialTheme.typography.headlineSmall)
        Text("Update the borrower, amount, date, description, and notes.")
        OutlinedTextField(
            value = borrower,
            onValueChange = { borrower = it },
            label = { Text("Borrower") },
            singleLine = true,
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = amount,
            onValueChange = { amount = it },
            label = { Text("Amount") },
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
            value = description,
            onValueChange = { description = it },
            label = { Text("Description") },
            modifier = Modifier.fillMaxWidth(),
        )
        OutlinedTextField(
            value = notes,
            onValueChange = { notes = it },
            label = { Text("Notes") },
            minLines = 7,
            modifier = Modifier.fillMaxWidth(),
        )
        error?.let { Text(it, color = androidx.compose.material3.MaterialTheme.colorScheme.error) }
        Button(onClick = ::save, modifier = Modifier.fillMaxWidth()) {
            Text("Done")
        }
    }

    if (showAmountConfirmation) {
        val newAmount = parseAmountText(amount) ?: loan.amount
        val difference = newAmount - loan.amount
        AlertDialog(
            onDismissRequest = { showAmountConfirmation = false },
            title = { Text("Confirm amount change") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text("The amount changes from ${money(loan.amount)} to ${money(newAmount)}.")
                    Text("Difference: ${if (difference >= 0) "+" else "−"}${money(abs(difference))}")
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    viewModel.updateLoan(loan.key, borrower, amount, description, date, notes)
                    showAmountConfirmation = false
                    onDone()
                }) {
                    Text("Confirm and save")
                }
            },
            dismissButton = {
                TextButton(onClick = { showAmountConfirmation = false }) {
                    Text("Back")
                }
            },
        )
    }
}
