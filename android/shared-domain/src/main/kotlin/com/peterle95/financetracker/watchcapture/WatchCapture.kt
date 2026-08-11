package com.peterle95.financetracker.watchcapture

import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.CategorySnapshot
import com.peterle95.financetracker.protocol.CategorySnapshotDefaults
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import com.peterle95.financetracker.protocol.TransactionProtocolValidator
import com.peterle95.financetracker.protocol.TransactionSubmission
import java.time.LocalDate
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
        TransactionProtocolValidator.submissionError(submission)?.let { throw IllegalArgumentException(it) }
        return submission
    }

    fun correct(input: WatchCaptureInput, rejectedSubmissionId: UUID, submissionId: UUID = UUID.randomUUID()): TransactionSubmission {
        require(submissionId != rejectedSubmissionId) { "Correction must use a new submission ID." }
        return create(input, submissionId)
    }
}

data class WatchCaptureForm(
    val type: SubmissionType,
    val amountText: String,
    val category: String,
    val description: String,
    val date: String,
    val isBnpl: Boolean,
)

object WatchCaptureFormLogic {
    fun initial(categories: CategorySnapshot = CategorySnapshotDefaults.snapshot(), today: String = LocalDate.now().toString()) =
        WatchCaptureForm(SubmissionType.Expense, "", categories.expenseCategories.firstOrNull().orEmpty(), "", today, true)

    fun categories(form: WatchCaptureForm, snapshot: CategorySnapshot) =
        if (form.type == SubmissionType.Expense) snapshot.expenseCategories else snapshot.incomeCategories

    fun switchType(form: WatchCaptureForm, type: SubmissionType, snapshot: CategorySnapshot): WatchCaptureForm {
        val categories = if (type == SubmissionType.Expense) snapshot.expenseCategories else snapshot.incomeCategories
        return form.copy(type = type, category = categories.firstOrNull().orEmpty(), isBnpl = type == SubmissionType.Expense)
    }

    fun refreshCategory(form: WatchCaptureForm, snapshot: CategorySnapshot): WatchCaptureForm {
        val categories = categories(form, snapshot)
        return if (form.category in categories) form else form.copy(category = categories.firstOrNull().orEmpty())
    }

    fun applyOutcome(
        form: WatchCaptureForm,
        acknowledgement: TransactionAcknowledgement,
        categories: CategorySnapshot,
        today: String = LocalDate.now().toString(),
    ) = if (acknowledgement.status == AcknowledgementStatus.Accepted) initial(categories, today) else form

    fun shouldApplyOutcome(current: WatchCaptureForm, submitted: WatchCaptureForm) = current == submitted

    fun shouldRestoreRejected(activeSubmissionId: String?, formTouched: Boolean) =
        activeSubmissionId == null && !formTouched

    fun rejectionText(code: String?, phoneMessage: String?): String {
        val message = phoneMessage?.trim()?.takeUnless { it.equals("Rejected", ignoreCase = true) || it.equals("Rejected.", ignoreCase = true) }
        return message ?: when (code) {
            "invalid_submission" -> "Check the amount, category, date, and BNPL setting."
            "unsupported_protocol" -> "Update the watch and phone apps."
            null -> "Transaction rejected."
            else -> "Transaction rejected ($code)."
        }
    }

    fun amountError(value: String): String? =
        if (value.trim().toDoubleOrNull()?.takeIf { it.isFinite() && it > 0.0 } == null) "Enter a positive amount." else null

    fun dateError(value: String): String? = when {
        !value.trim().matches(Regex("\\d{4}-\\d{2}-\\d{2}")) -> "Use YYYY-MM-DD."
        runCatching { LocalDate.parse(value.trim()) }.isFailure -> "Enter a real calendar date."
        else -> null
    }

    fun categoryError(value: String): String? = when {
        value.isBlank() -> "Choose a category."
        value.length > 100 -> "Category is too long."
        else -> null
    }

    fun canSubmit(form: WatchCaptureForm) =
        amountError(form.amountText) == null && categoryError(form.category) == null && dateError(form.date) == null &&
            !(form.isBnpl && form.type != SubmissionType.Expense)
}
