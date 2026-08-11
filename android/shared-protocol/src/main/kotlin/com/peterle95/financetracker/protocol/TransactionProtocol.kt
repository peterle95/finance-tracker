package com.peterle95.financetracker.protocol

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.doubleOrNull
import kotlinx.serialization.json.jsonPrimitive
import kotlinx.serialization.json.put
import java.time.LocalDate
import java.util.UUID

const val TRANSACTION_SUBMISSIONS_PATH = "/finance/v1/transaction-submissions"
const val TRANSACTION_ACKNOWLEDGEMENTS_PATH = "/finance/v1/transaction-acknowledgements"
const val PROTOCOL_VERSION = 1

enum class SubmissionType { Expense, Income }

enum class AcknowledgementStatus { Accepted, Duplicate, Rejected }

data class TransactionSubmission(
    val protocolVersion: Int = PROTOCOL_VERSION,
    val submissionId: UUID,
    val type: SubmissionType,
    val amount: Double,
    val category: String,
    val description: String,
    val transactionDate: String,
    val isBnpl: Boolean,
)

data class TransactionAcknowledgement(
    val protocolVersion: Int = PROTOCOL_VERSION,
    val submissionId: UUID,
    val status: AcknowledgementStatus,
    val code: String? = null,
    val message: String? = null,
)

object TransactionProtocolValidator {
    fun submissionError(submission: TransactionSubmission): String? = when {
        submission.protocolVersion != PROTOCOL_VERSION -> "Unsupported protocol version."
        !submission.amount.isFinite() || submission.amount <= 0.0 -> "Amount must be a positive finite number."
        submission.category.isBlank() -> "Category is required."
        submission.category.length > MAX_CATEGORY_LENGTH -> "Category is too long."
        !isIsoDate(submission.transactionDate) -> "Date must use YYYY-MM-DD."
        submission.isBnpl && submission.type != SubmissionType.Expense -> "BNPL is only available for expenses."
        else -> null
    }

    fun acknowledgementError(acknowledgement: TransactionAcknowledgement): String? =
        if (acknowledgement.protocolVersion != PROTOCOL_VERSION) "Unsupported protocol version." else null

    private fun isIsoDate(value: String): Boolean =
        value.matches(Regex("\\d{4}-\\d{2}-\\d{2}")) && runCatching { LocalDate.parse(value) }.isSuccess

    private const val MAX_CATEGORY_LENGTH = 100
}

object TransactionProtocolCodec {
    private val json = Json

    fun encodeSubmission(submission: TransactionSubmission): ByteArray {
        require(TransactionProtocolValidator.submissionError(submission) == null)
        return json.encodeToString(JsonObject.serializer(), buildJsonObject {
            put("protocolVersion", submission.protocolVersion)
            put("submissionId", submission.submissionId.toString())
            put("type", submission.type.name)
            put("amount", submission.amount)
            put("category", submission.category)
            put("description", submission.description.trim())
            put("transactionDate", submission.transactionDate)
            put("isBnpl", submission.isBnpl)
        }).encodeToByteArray()
    }

    fun decodeSubmission(payload: ByteArray): TransactionSubmission? = runCatching {
        val value = json.parseToJsonElement(payload.decodeToString()) as? JsonObject ?: return null
        if (value.keys != submissionKeys) return null
        val amount = value["amount"]?.jsonPrimitive ?: return null
        if (amount.isString) return null
        TransactionSubmission(
            protocolVersion = value.int("protocolVersion") ?: return null,
            submissionId = UUID.fromString(value.string("submissionId") ?: return null),
            type = SubmissionType.entries.firstOrNull { it.name == value.string("type") } ?: return null,
            amount = amount.doubleOrNull ?: return null,
            category = value.string("category") ?: return null,
            description = value.string("description")?.trim() ?: return null,
            transactionDate = value.string("transactionDate") ?: return null,
            isBnpl = value["isBnpl"]?.jsonPrimitive?.booleanOrNull ?: return null,
        ).takeIf { TransactionProtocolValidator.submissionError(it) == null }
    }.getOrNull()

    fun encodeAcknowledgement(acknowledgement: TransactionAcknowledgement): ByteArray {
        require(TransactionProtocolValidator.acknowledgementError(acknowledgement) == null)
        return json.encodeToString(JsonObject.serializer(), buildJsonObject {
            put("protocolVersion", acknowledgement.protocolVersion)
            put("submissionId", acknowledgement.submissionId.toString())
            put("status", acknowledgement.status.name)
            acknowledgement.code?.let { put("code", it) }
            acknowledgement.message?.let { put("message", it) }
        }).encodeToByteArray()
    }

    fun decodeAcknowledgement(payload: ByteArray): TransactionAcknowledgement? = runCatching {
        val value = json.parseToJsonElement(payload.decodeToString()) as? JsonObject ?: return null
        if (!value.keys.all { it in acknowledgementKeys } || !requiredAcknowledgementKeys.all { it in value }) return null
        TransactionAcknowledgement(
            protocolVersion = value.int("protocolVersion") ?: return null,
            submissionId = UUID.fromString(value.string("submissionId") ?: return null),
            status = AcknowledgementStatus.entries.firstOrNull { it.name == value.string("status") } ?: return null,
            code = value.string("code"),
            message = value.string("message"),
        ).takeIf { TransactionProtocolValidator.acknowledgementError(it) == null }
    }.getOrNull()

    private fun JsonObject.string(name: String): String? =
        this[name]?.jsonPrimitive?.takeIf { it.isString }?.contentOrNull

    private fun JsonObject.int(name: String): Int? =
        this[name]?.jsonPrimitive?.takeUnless(JsonPrimitive::isString)?.contentOrNull?.toIntOrNull()

    private val submissionKeys = setOf(
        "protocolVersion", "submissionId", "type", "amount", "category", "description", "transactionDate", "isBnpl",
    )
    private val requiredAcknowledgementKeys = setOf("protocolVersion", "submissionId", "status")
    private val acknowledgementKeys = requiredAcknowledgementKeys + setOf("code", "message")
}
