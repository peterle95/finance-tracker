package com.peterle95.financetracker.data

import android.content.Context
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.domain.TransactionUiLogic
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.PROTOCOL_VERSION
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import com.peterle95.financetracker.protocol.TransactionSubmission
import java.time.LocalDate
import java.util.UUID
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

interface SubmissionLedger {
    fun transactionId(submissionId: UUID): String?
    fun save(submissionId: UUID, transactionId: String)
}

class SharedPreferencesSubmissionLedger(context: Context) : SubmissionLedger {
    private val preferences = context.getSharedPreferences("watch_submission_ledger", Context.MODE_PRIVATE)

    override fun transactionId(submissionId: UUID): String? = entries()[submissionId.toString()]

    override fun save(submissionId: UUID, transactionId: String) {
        preferences.edit().putStringSet(
            "entries",
            (entries() + (submissionId.toString() to transactionId)).map { "${it.key}=${it.value}" }.toSet(),
        ).commit()
    }

    private fun entries(): Map<String, String> = preferences.getStringSet("entries", emptySet()).orEmpty().mapNotNull {
        val (submissionId, transactionId) = it.split('=', limit = 2)
        transactionId.takeIf(String::isNotBlank)?.let { id -> submissionId to id }
    }.toMap()
}

class PhoneTransactionIntake(
    private val store: FinanceDirectoryStore,
    private val ledger: SubmissionLedger = InMemorySubmissionLedger(),
) {
    private val mutex = Mutex()

    suspend fun intake(submission: TransactionSubmission): TransactionAcknowledgement = mutex.withLock {
        submissionError(submission)?.let { return rejected(submission, it) }
        val transactionId = ledger.transactionId(submission.submissionId)
        if (transactionId != null && store.containsTransaction(transactionId)) {
            return TransactionAcknowledgement(submissionId = submission.submissionId, status = AcknowledgementStatus.Duplicate)
        }
        return try {
            val dates = TransactionUiLogic.bookingDatesFor(
                type = TransactionType.valueOf(submission.type.name),
                selectedDate = submission.transactionDate,
                isBnpl = submission.isBnpl,
            )
            store.addTransaction(
                type = TransactionType.valueOf(submission.type.name),
                date = dates.date,
                amount = submission.amount,
                category = submission.category,
                description = submission.description.trim(),
                behaviorDate = dates.behaviorDate,
                transactionId = transactionId ?: UUID.randomUUID().toString().also { ledger.save(submission.submissionId, it) },
            )
            TransactionAcknowledgement(submissionId = submission.submissionId, status = AcknowledgementStatus.Accepted)
        } catch (error: Throwable) {
            rejected(submission, error.message ?: "Could not write transaction.", "write_failed")
        }
    }

    private fun submissionError(submission: TransactionSubmission): String? = when {
        submission.protocolVersion != PROTOCOL_VERSION -> "Unsupported protocol version."
        !submission.amount.isFinite() || submission.amount <= 0.0 -> "Amount must be a positive finite number."
        submission.category.isBlank() -> "Category is required."
        !submission.transactionDate.matches(Regex("\\d{4}-\\d{2}-\\d{2}")) -> "Date must use YYYY-MM-DD."
        runCatching { LocalDate.parse(submission.transactionDate) }.isFailure -> "Date must use YYYY-MM-DD."
        submission.isBnpl && submission.type != SubmissionType.Expense -> "BNPL is only available for expenses."
        else -> null
    }

    private fun rejected(
        submission: TransactionSubmission,
        message: String,
        code: String = "invalid_submission",
    ) = TransactionAcknowledgement(
        submissionId = submission.submissionId,
        status = AcknowledgementStatus.Rejected,
        code = code,
        message = message,
    )
}

private class InMemorySubmissionLedger : SubmissionLedger {
    private val entries = mutableMapOf<UUID, String>()

    override fun transactionId(submissionId: UUID): String? = entries[submissionId]

    override fun save(submissionId: UUID, transactionId: String) {
        entries[submissionId] = transactionId
    }
}
