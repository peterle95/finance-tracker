package com.peterle95.financetracker.wear

import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.UUID

class WatchDeliveryTest {
    @Test
    fun outcomeQueueDoesNotConflateRapidAcknowledgements() = runBlocking {
        val queue = WatchOutcomeQueue()
        val outcomes = listOf(
            TransactionAcknowledgement(submissionId = UUID.randomUUID(), status = AcknowledgementStatus.Accepted),
            TransactionAcknowledgement(submissionId = UUID.randomUUID(), status = AcknowledgementStatus.Rejected),
        )

        outcomes.forEach(queue::send)

        assertEquals(outcomes, queue.outcomes().take(outcomes.size).toList())
    }

    @Test
    fun noPendingSubmissionSucceeds() {
        assertEquals(DeliveryResult.Success, deliveryResult(DeliveryAttempt.NotNeeded, hasPending = false))
    }

    @Test
    fun unreachablePhoneOrSendFailureRetries() {
        assertEquals(DeliveryResult.Retry, deliveryResult(DeliveryAttempt.Failed, hasPending = false))
    }

    @Test
    fun successfulSendWithoutAcknowledgementRetries() {
        assertEquals(DeliveryResult.Retry, deliveryResult(DeliveryAttempt.Succeeded, hasPending = true))
    }

    @Test
    fun terminalAcknowledgementSucceeds() {
        assertEquals(DeliveryResult.Success, deliveryResult(DeliveryAttempt.Succeeded, hasPending = false))
    }

    @Test
    fun acknowledgementTransitionsOnlyMatchingRow() = runBlocking {
        val id = UUID.randomUUID()
        val rows = mutableMapOf(id.toString() to WatchOutboxRow(id.toString(), "payload"))
        suspend fun transition(status: AcknowledgementStatus, submissionId: UUID = id) = transitionAcknowledgementRow(
            TransactionAcknowledgement(submissionId = submissionId, status = status, code = "invalid_submission", message = "Fix it"),
            row = { rows[it] },
            delete = { rows.remove(it) != null },
            reject = { rowId, message ->
                rows[rowId]?.let { rows[rowId] = it.copy(state = "rejected", message = message) } != null
            },
        )

        assertTrue(transition(AcknowledgementStatus.Accepted))
        assertFalse(rows.containsKey(id.toString()))

        rows[id.toString()] = WatchOutboxRow(id.toString(), "payload")
        assertTrue(transition(AcknowledgementStatus.Duplicate))
        assertFalse(rows.containsKey(id.toString()))

        rows[id.toString()] = WatchOutboxRow(id.toString(), "payload")
        assertTrue(transition(AcknowledgementStatus.Rejected))
        assertEquals("rejected", rows[id.toString()]?.state)
        assertEquals("Fix it", rows[id.toString()]?.message)

        val unchanged = rows.toMap()
        assertFalse(transition(AcknowledgementStatus.Accepted, UUID.randomUUID()))
        assertEquals(unchanged, rows)
    }
}
