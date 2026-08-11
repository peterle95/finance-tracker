package com.peterle95.financetracker.watchcapture

import com.peterle95.financetracker.protocol.CategorySnapshot
import com.peterle95.financetracker.protocol.CategorySnapshotDefaults
import com.peterle95.financetracker.protocol.SubmissionType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

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
}
