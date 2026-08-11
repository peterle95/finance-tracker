package com.peterle95.financetracker.protocol

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.util.UUID

class TransactionProtocolCodecTest {
    @Test
    fun submissionRoundTripNormalizesDescription() {
        val submission = TransactionSubmission(
            submissionId = UUID.fromString("d2719dc4-0b6f-4a9f-a7ba-7bad97f57958"),
            type = SubmissionType.Expense,
            amount = 12.5,
            category = "Food",
            description = "  Lunch  ",
            transactionDate = "2026-08-11",
            isBnpl = true,
        )

        val decoded = TransactionProtocolCodec.decodeSubmission(TransactionProtocolCodec.encodeSubmission(submission))

        assertEquals(submission.copy(description = "Lunch"), decoded)
    }

    @Test
    fun invalidOrUnknownSubmissionDataIsRejected() {
        assertNull(TransactionProtocolCodec.decodeSubmission("""{"protocolVersion":2}""".encodeToByteArray()))
        assertNull(
            TransactionProtocolCodec.decodeSubmission(
                """{"protocolVersion":1,"submissionId":"d2719dc4-0b6f-4a9f-a7ba-7bad97f57958","type":"Transfer","amount":1,"category":"Food","description":"","transactionDate":"2026-08-11","isBnpl":false}"""
                    .encodeToByteArray(),
            ),
        )
        assertNull(
            TransactionProtocolCodec.decodeSubmission(
                """{"protocolVersion":1,"submissionId":"d2719dc4-0b6f-4a9f-a7ba-7bad97f57958","type":"Expense","amount":"1","category":"Food","description":"","transactionDate":"2026-08-11","isBnpl":false}"""
                    .encodeToByteArray(),
            ),
        )
    }

    @Test
    fun categoryAllowsStaleLabelsButBoundsUntrustedInput() {
        val submission = TransactionSubmission(
            submissionId = UUID.randomUUID(),
            type = SubmissionType.Expense,
            amount = 1.0,
            category = "Stale category",
            description = "",
            transactionDate = "2026-08-11",
            isBnpl = false,
        )

        assertNull(TransactionProtocolValidator.submissionError(submission))
        assertEquals("Category is too long.", TransactionProtocolValidator.submissionError(submission.copy(category = "a".repeat(101))))
    }

    @Test
    fun acknowledgementRoundTripsAndRejectsUnknownStatus() {
        val acknowledgement = TransactionAcknowledgement(
            submissionId = UUID.fromString("d2719dc4-0b6f-4a9f-a7ba-7bad97f57958"),
            status = AcknowledgementStatus.Accepted,
        )

        assertEquals(
            acknowledgement,
            TransactionProtocolCodec.decodeAcknowledgement(TransactionProtocolCodec.encodeAcknowledgement(acknowledgement)),
        )
        assertNull(TransactionProtocolCodec.decodeAcknowledgement("""{"protocolVersion":1,"submissionId":"d2719dc4-0b6f-4a9f-a7ba-7bad97f57958","status":"queued"}""".encodeToByteArray()))
    }
}
