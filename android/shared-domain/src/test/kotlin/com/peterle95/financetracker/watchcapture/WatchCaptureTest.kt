package com.peterle95.financetracker.watchcapture

import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.CategorySnapshot
import com.peterle95.financetracker.protocol.CategorySnapshotDefaults
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class WatchCaptureTest {
    private val categories = CategorySnapshot(
        revision = 3,
        expenseCategories = listOf("Phone expense", "Other"),
        incomeCategories = listOf("Phone income"),
    )

    @Test
    fun expenseDefaultsUseTodayFirstPhoneCategoryAndBnpl() {
        val form = WatchCaptureFormLogic.initial(categories, "2026-08-11")

        assertEquals(SubmissionType.Expense, form.type)
        assertEquals("Phone expense", form.category)
        assertEquals("2026-08-11", form.date)
        assertTrue(form.isBnpl)
    }

    @Test
    fun typeSwitchRefreshesCategoryAndBnpl() {
        val income = WatchCaptureFormLogic.switchType(WatchCaptureFormLogic.initial(categories), SubmissionType.Income, categories)

        assertEquals(listOf("Phone income"), WatchCaptureFormLogic.categories(income, categories))
        assertEquals("Phone income", income.category)
        assertFalse(income.isBnpl)
        assertTrue(WatchCaptureFormLogic.switchType(income, SubmissionType.Expense, categories).isBnpl)
    }

    @Test
    fun categoryRefreshPreservesCurrentSelection() {
        val form = WatchCaptureFormLogic.initial(categories).copy(category = "Other")

        assertEquals("Other", WatchCaptureFormLogic.refreshCategory(form, categories).category)
    }

    @Test
    fun categoryRefreshReplacesStaleSelection() {
        val form = WatchCaptureFormLogic.initial(categories).copy(category = "Removed")

        assertEquals("Phone expense", WatchCaptureFormLogic.refreshCategory(form, categories).category)
    }

    @Test
    fun formValidationRequiresPositiveAmountCategoryAndRealDate() {
        val valid = WatchCaptureFormLogic.initial(categories, "2026-08-11").copy(amountText = "12.50")

        assertTrue(WatchCaptureFormLogic.canSubmit(valid))
        assertFalse(WatchCaptureFormLogic.canSubmit(valid.copy(amountText = "0")))
        assertFalse(WatchCaptureFormLogic.canSubmit(valid.copy(category = "")))
        assertEquals("Use YYYY-MM-DD.", WatchCaptureFormLogic.dateError("11/08/2026"))
        assertEquals("Enter a real calendar date.", WatchCaptureFormLogic.dateError("2026-02-30"))
        assertNull(WatchCaptureFormLogic.dateError("2026-02-28"))
    }

    @Test
    fun unavailableSnapshotUsesSchemaDefaults() {
        val form = WatchCaptureFormLogic.initial(today = "2026-08-11")

        assertEquals(CategorySnapshotDefaults.expenseCategories.first(), form.category)
        assertEquals(
            CategorySnapshotDefaults.incomeCategories,
            WatchCaptureFormLogic.categories(
                WatchCaptureFormLogic.switchType(form, SubmissionType.Income, CategorySnapshotDefaults.snapshot()),
                CategorySnapshotDefaults.snapshot(),
            ),
        )
    }

    @Test
    fun submissionTrimsOptionalDescription() {
        val submission = WatchCaptureSubmission.create(
            WatchCaptureInput(SubmissionType.Income, " 12.5 ", "Phone income", "  Pay  ", " 2026-08-11 "),
        )

        assertEquals("Pay", submission.description)
        assertEquals("2026-08-11", submission.transactionDate)
    }

    @Test
    fun acceptedOutcomeResetsWholeFormToCurrentDefaults() {
        val form = WatchCaptureForm(SubmissionType.Income, "12.50", "Old", "Pay", "2026-08-01", false)
        val acknowledgement = TransactionAcknowledgement(
            submissionId = UUID.randomUUID(),
            status = AcknowledgementStatus.Accepted,
        )

        assertEquals(WatchCaptureFormLogic.initial(categories, "2026-08-11"), WatchCaptureFormLogic.applyOutcome(form, acknowledgement, categories, "2026-08-11"))
    }

    @Test
    fun duplicateAndRejectedOutcomesPreserveEveryField() {
        val form = WatchCaptureForm(SubmissionType.Expense, "012.50", "Removed", " Lunch ", "2026-08-01", true)

        listOf(AcknowledgementStatus.Duplicate, AcknowledgementStatus.Rejected).forEach { status ->
            val acknowledgement = TransactionAcknowledgement(submissionId = UUID.randomUUID(), status = status)
            assertEquals(form, WatchCaptureFormLogic.applyOutcome(form, acknowledgement, categories, "2026-08-11"))
        }
    }

    @Test
    fun outcomeOnlyChangesTheSubmittedForm() {
        val submitted = WatchCaptureForm(SubmissionType.Expense, "12.50", "Phone expense", "Lunch", "2026-08-11", true)

        assertTrue(WatchCaptureFormLogic.shouldApplyOutcome(submitted, submitted))
        assertFalse(WatchCaptureFormLogic.shouldApplyOutcome(submitted.copy(description = "Dinner"), submitted))
    }

    @Test
    fun rejectedPayloadOnlyRestoresOverUntouchedInactiveForm() {
        assertTrue(WatchCaptureFormLogic.shouldRestoreRejected(activeSubmissionId = null, formTouched = false))
        assertFalse(WatchCaptureFormLogic.shouldRestoreRejected(activeSubmissionId = "active", formTouched = false))
        assertFalse(WatchCaptureFormLogic.shouldRestoreRejected(activeSubmissionId = null, formTouched = true))
    }

    @Test
    fun rejectionTextUsesUsefulPhoneMessageAndCodeFallback() {
        assertEquals("Amount must be positive.", WatchCaptureFormLogic.rejectionText("invalid_submission", "Amount must be positive."))
        assertEquals(
            "Check the amount, category, date, and BNPL setting.",
            WatchCaptureFormLogic.rejectionText("invalid_submission", "Rejected."),
        )
    }

    @Test
    fun correctionRequiresFreshUuidAtSubmissionSeam() {
        val oldId = UUID.randomUUID()
        val newId = UUID.randomUUID()
        val input = WatchCaptureInput(SubmissionType.Expense, "12.5", "Phone expense", "Lunch", "2026-08-11", true)

        assertEquals(newId, WatchCaptureSubmission.correct(input, oldId, newId).submissionId)
        assertTrue(runCatching { WatchCaptureSubmission.correct(input, oldId, oldId) }.isFailure)
    }
}
