package com.peterle95.financetracker.data

import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionSubmission
import kotlinx.coroutines.runBlocking
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonArray
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class PhoneTransactionIntakeTest {
    @Test
    fun acceptedBnplIsOwnedByCategoryWithIndependentIdAndDuplicateDoesNotRewrite() = runBlocking {
        val legacy = """
            {"expenses":[],"incomes":[],"categories":{"Expense":["Food"],"Income":["Salary"]},"budget_settings":{}}
        """.trimIndent()
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.clearWrites()
        val ledger = InMemorySubmissionLedger()
        val intake = PhoneTransactionIntake(store, ledger)
        val submission = TransactionSubmission(
            submissionId = UUID.fromString("d2719dc4-0b6f-4a9f-a7ba-7bad97f57958"),
            type = SubmissionType.Expense,
            amount = 12.5,
            category = "Food",
            description = " Lunch ",
            transactionDate = "2026-08-11",
            isBnpl = true,
        )

        assertEquals(AcknowledgementStatus.Accepted, intake.intake(submission)?.status)
        val row = directory.element("transactions_expense_food.json").jsonArray.single().jsonObject
        assertEquals("2026-09-01", row["date"]!!.jsonPrimitive.content)
        assertEquals("2026-08-11", row["behavior_date"]!!.jsonPrimitive.content)
        assertEquals("Lunch", row["description"]!!.jsonPrimitive.content)
        assertNotEquals(submission.submissionId.toString(), row["id"]!!.jsonPrimitive.content)
        assertEquals(legacy, directory.files.getValue("finance_data.json"))
        assertFalse(directory.files.values.any { it.contains(submission.submissionId.toString()) })

        directory.clearWrites()
        assertEquals(AcknowledgementStatus.Duplicate, PhoneTransactionIntake(store, ledger).intake(submission)?.status)
        assertTrue(directory.writes.isEmpty())
        assertEquals(1, directory.element("transactions_expense_food.json").jsonArray.size)
        assertEquals(SubmissionOutcome.Accepted, ledger.entry(submission.submissionId)?.outcome)
        assertNull(ledger.entry(submission.submissionId)?.payload)
    }

    @Test
    fun pendingLedgerReconcilesWrittenTransactionWithoutAnotherWrite() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy()))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val ledger = InMemorySubmissionLedger()
        val submission = submission(category = "Food")
        val transactionId = "written-before-crash"
        ledger.createPending(submission, transactionId)
        store.addTransaction(
            com.peterle95.financetracker.domain.TransactionType.Expense,
            "2026-08-11",
            4.0,
            "Food",
            "Lunch",
            null,
            transactionId,
        )
        directory.clearWrites()

        assertEquals(AcknowledgementStatus.Duplicate, PhoneTransactionIntake(store, ledger).intake(submission)?.status)
        assertTrue(directory.writes.isEmpty())
        assertEquals(SubmissionOutcome.Duplicate, ledger.entry(submission.submissionId)?.outcome)
        assertNull(ledger.entry(submission.submissionId)?.payload)
    }

    @Test
    fun recoverableWriteFailureStaysPendingAndRetries() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy()))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val ledger = InMemorySubmissionLedger()
        val submission = submission(category = "Food")
        directory.failWrites = true

        assertNull(PhoneTransactionIntake(store, ledger).intake(submission))
        assertEquals(SubmissionOutcome.Pending, ledger.entry(submission.submissionId)?.outcome)
        assertNull(ledger.entry(submission.submissionId)?.payload)
        directory.failWrites = false
        assertEquals(AcknowledgementStatus.Accepted, PhoneTransactionIntake(store, ledger).intake(submission)?.status)
        assertEquals(1, directory.element("transactions_expense_food.json").jsonArray.size)
    }

    @Test
    fun ledgerOmitsPayloadAndAcceptsStaleCategory() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy()))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val ledger = InMemorySubmissionLedger()
        val submission = submission(category = "Stale category")

        assertEquals(AcknowledgementStatus.Accepted, PhoneTransactionIntake(store, ledger).intake(submission)?.status)
        val entry = ledger.entry(submission.submissionId)
        assertEquals(SubmissionOutcome.Accepted, entry?.outcome)
        assertNull(entry?.payload)
        assertTrue(entry?.transactionId?.isNotBlank() == true)
        assertTrue(directory.files.containsKey("transactions_expense_stale-category.json"))
    }

    @Test
    fun paddedRegisteredCategoryReusesExistingCategoryAndReloads() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy()))
        val store = FinanceDirectoryStore(directory)
        store.reload()

        assertEquals(
            AcknowledgementStatus.Accepted,
            PhoneTransactionIntake(store, InMemorySubmissionLedger()).intake(submission(category = "  Food  "))?.status,
        )
        assertEquals(1, directory.element("categories.json").jsonObject["Expense"]!!.jsonArray.size)
        assertEquals(1, directory.element("transactions_expense_food.json").jsonArray.size)
        assertFalse(directory.files.containsKey("transactions_expense_food-2.json"))
        assertEquals(1, FinanceDirectoryStore(directory).reload().document.transactions.size)
    }

    @Test
    fun invalidSubmissionIsRejectedWithoutWriting() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to "{\"expenses\":[],\"incomes\":[],\"categories\":{\"Expense\":[\"Food\"],\"Income\":[]},\"budget_settings\":{}}"))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        directory.clearWrites()

        val ledger = InMemorySubmissionLedger()
        val submission = TransactionSubmission(
            submissionId = UUID.randomUUID(),
            type = SubmissionType.Expense,
            amount = -1.0,
            category = "Food",
            description = "Bad",
            transactionDate = "2026-08-11",
            isBnpl = false,
        )
        val acknowledgement = PhoneTransactionIntake(store, ledger).intake(
            submission,
        )

        assertEquals(AcknowledgementStatus.Rejected, acknowledgement?.status)
        assertEquals("invalid_submission", acknowledgement?.code)
        assertEquals("Amount must be a positive finite number.", acknowledgement?.message)
        assertTrue(directory.writes.isEmpty())
        assertEquals(SubmissionOutcome.Rejected, ledger.entry(submission.submissionId)?.outcome)
        assertNull(ledger.entry(submission.submissionId)?.payload)

        directory.clearWrites()
        val retry = PhoneTransactionIntake(store, ledger).intake(submission)
        assertEquals(AcknowledgementStatus.Rejected, retry?.status)
        assertEquals("invalid_submission", retry?.code)
        assertEquals("Amount must be a positive finite number.", retry?.message)
        assertTrue(directory.writes.isEmpty())
    }

    @Test
    fun incomeUsesIncomeCategoryAndRejectsBnpl() = runBlocking {
        val directory = InMemoryFinanceDirectory(mutableMapOf("finance_data.json" to legacy()))
        val store = FinanceDirectoryStore(directory)
        store.reload()
        val intake = PhoneTransactionIntake(store, InMemorySubmissionLedger())
        val income = submission(category = "Old income").copy(type = SubmissionType.Income, description = "  Pay  ")

        assertEquals(AcknowledgementStatus.Accepted, intake.intake(income)?.status)
        val row = directory.element("transactions_income_old-income.json").jsonArray.single().jsonObject
        assertEquals("2026-08-11", row["date"]!!.jsonPrimitive.content)
        assertEquals("Pay", row["description"]!!.jsonPrimitive.content)
        assertEquals(
            AcknowledgementStatus.Rejected,
            intake.intake(income.copy(submissionId = UUID.randomUUID(), isBnpl = true))?.status,
        )
    }

    @Test
    fun legacyLedgerRowsPreserveIdsAsPendingWithoutPayload() {
        val submissionId = UUID.randomUUID()

        val row = legacyLedgerRows(setOf("$submissionId=existing-transaction", "invalid=missing")).single()

        assertEquals(submissionId.toString(), row.submissionId)
        assertEquals("existing-transaction", row.transactionId)
        assertEquals(SubmissionOutcome.Pending.name, row.outcome)
        assertNull(row.payload)
    }

    private fun legacy() = """
        {"expenses":[],"incomes":[],"categories":{"Expense":["Food"],"Income":["Salary"]},"budget_settings":{}}
    """.trimIndent()

    private fun submission(category: String) = TransactionSubmission(
        submissionId = UUID.randomUUID(),
        type = SubmissionType.Expense,
        amount = 4.0,
        category = category,
        description = "Lunch",
        transactionDate = "2026-08-11",
        isBnpl = false,
    )

    private class InMemoryFinanceDirectory(
        val files: MutableMap<String, String>,
        var failWrites: Boolean = false,
    ) : FinanceDirectory {
        val writes = mutableListOf<String>()

        override suspend fun listFiles() = files.keys.toList()
        override suspend fun readText(name: String) = files[name]
        override suspend fun writeText(name: String, content: String) {
            if (failWrites) error("Storage unavailable")
            writes += name
            files[name] = content
        }

        override suspend fun delete(name: String) {
            files.remove(name)
        }

        fun clearWrites() {
            writes.clear()
        }

        fun element(name: String) = Json.parseToJsonElement(files.getValue(name))
    }
}
