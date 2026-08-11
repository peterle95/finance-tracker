package com.peterle95.financetracker.watchcapture

import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionProtocolValidator
import com.peterle95.financetracker.protocol.TransactionSubmission
import java.util.UUID

data class WatchCaptureInput(
    val type: SubmissionType,
    val amountText: String,
    val category: String,
    val description: String,
    val date: String,
    val isBnpl: Boolean = false,
)

object WatchCaptureSubmission {
    fun create(input: WatchCaptureInput, submissionId: UUID = UUID.randomUUID()): TransactionSubmission {
        val submission = TransactionSubmission(
            submissionId = submissionId,
            type = input.type,
            amount = input.amountText.trim().toDoubleOrNull() ?: error("Amount must be a number."),
            category = input.category,
            description = input.description.trim(),
            transactionDate = input.date.trim(),
            isBnpl = input.isBnpl,
        )
        require(TransactionProtocolValidator.submissionError(submission) == null) { "Invalid watch capture." }
        return submission
    }
}

object WatchCaptureCategories {
    val expense = listOf("Food", "Transportation", "Entertainment", "Utilities", "Shopping", "Healthcare", "Money Lent", "Other")
}
