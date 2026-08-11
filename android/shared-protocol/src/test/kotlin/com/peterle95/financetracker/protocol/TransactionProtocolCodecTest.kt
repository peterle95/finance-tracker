package com.peterle95.financetracker.protocol

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
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
    fun submissionPayloadIsCappedBelowDataLayerLimit() {
        val submission = TransactionSubmission(
            submissionId = UUID.randomUUID(),
            type = SubmissionType.Expense,
            amount = 1.0,
            category = "Food",
            description = "x".repeat(100_000),
            transactionDate = "2026-08-11",
            isBnpl = false,
        )

        assertThrows(IllegalArgumentException::class.java) {
            TransactionProtocolCodec.encodeSubmission(submission)
        }
        val payload = """{"protocolVersion":1,"submissionId":"${submission.submissionId}","type":"Expense","amount":1,"category":"Food","description":"${submission.description}","transactionDate":"2026-08-11","isBnpl":false}"""
            .encodeToByteArray()
        assertNull(TransactionProtocolCodec.decodeSubmission(payload))
    }

    @Test
    fun structurallyValidInvalidFieldsReachPhoneValidation() {
        val payload = """{"protocolVersion":1,"submissionId":"d2719dc4-0b6f-4a9f-a7ba-7bad97f57958","type":"Income","amount":-1,"category":"Salary","description":"","transactionDate":"bad","isBnpl":true}"""

        val submission = requireNotNull(TransactionProtocolCodec.decodeSubmission(payload.encodeToByteArray()))

        assertEquals("Amount must be a positive finite number.", TransactionProtocolValidator.submissionError(submission))
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

    @Test
    fun categorySnapshotRoundTripsStrictSchema() {
        val snapshot = CategorySnapshot(
            revision = 7,
            expenseCategories = listOf("Food", "Travel"),
            incomeCategories = listOf("Salary"),
        )

        assertEquals(snapshot, TransactionProtocolCodec.decodeCategories(TransactionProtocolCodec.encodeCategories(snapshot)))
        assertNull(TransactionProtocolCodec.decodeCategories("""{"schemaVersion":1,"revision":7,"expenseCategories":["Food"],"incomeCategories":[],"extra":true}""".encodeToByteArray()))
        assertNull(TransactionProtocolCodec.decodeCategories("""{"schemaVersion":2,"revision":7,"expenseCategories":["Food"],"incomeCategories":[]}""".encodeToByteArray()))
        assertNull(TransactionProtocolCodec.decodeCategories("""{"schemaVersion":1,"revision":-1,"expenseCategories":["Food"],"incomeCategories":[]}""".encodeToByteArray()))
        assertNull(TransactionProtocolCodec.decodeCategories("""{"schemaVersion":1,"revision":7,"expenseCategories":["Food","food"],"incomeCategories":[]}""".encodeToByteArray()))
        assertNull(TransactionProtocolCodec.decodeCategories("""{"schemaVersion":1,"revision":7,"expenseCategories":[1],"incomeCategories":[]}""".encodeToByteArray()))
    }

    @Test
    fun categoryPayloadIsCappedBelowDataLayerLimit() {
        assertThrows(IllegalArgumentException::class.java) {
            TransactionProtocolCodec.encodeCategories(
                CategorySnapshot(
                    revision = 1,
                    expenseCategories = (1..1_100).map { "category-$it-${"x".repeat(80)}" },
                    incomeCategories = emptyList(),
                ),
            )
        }
    }
}
