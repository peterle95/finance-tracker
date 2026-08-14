package com.peterle95.financetracker.data

import android.content.Context
import androidx.room.Dao
import androidx.room.Database
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.Transaction
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.domain.TransactionUiLogic
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import com.peterle95.financetracker.protocol.TransactionProtocolValidator
import com.peterle95.financetracker.protocol.TransactionSubmission
import java.util.UUID
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

enum class SubmissionOutcome { Pending, Accepted, Duplicate, Rejected }

data class SubmissionLedgerEntry(
    val submissionId: UUID,
    val transactionId: String,
    val outcome: SubmissionOutcome,
    val payload: String?,
    val code: String? = null,
    val message: String? = null,
)

interface SubmissionLedger {
    suspend fun entry(submissionId: UUID): SubmissionLedgerEntry?
    suspend fun createPending(submission: TransactionSubmission, transactionId: String): SubmissionLedgerEntry
    suspend fun finish(submissionId: UUID, outcome: SubmissionOutcome, code: String? = null, message: String? = null)
}

@Entity(tableName = "watch_submission_ledger")
data class SubmissionLedgerRow(
    @androidx.room.PrimaryKey val submissionId: String,
    val transactionId: String,
    val outcome: String,
    val payload: String?,
    val code: String?,
    val message: String?,
)

@Dao
abstract class SubmissionLedgerDao {
    @Query("SELECT * FROM watch_submission_ledger WHERE submissionId = :submissionId")
    abstract suspend fun row(submissionId: String): SubmissionLedgerRow?

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    abstract suspend fun insert(row: SubmissionLedgerRow)

    @Query("UPDATE watch_submission_ledger SET outcome = :outcome, payload = NULL, code = :code, message = :message WHERE submissionId = :submissionId")
    abstract suspend fun finish(submissionId: String, outcome: String, code: String?, message: String?)

    @Transaction
    open suspend fun getOrCreate(row: SubmissionLedgerRow): SubmissionLedgerRow {
        insert(row)
        return requireNotNull(this.row(row.submissionId))
    }
}

@Database(entities = [SubmissionLedgerRow::class], version = 1, exportSchema = false)
abstract class SubmissionLedgerDatabase : RoomDatabase() {
    abstract fun ledger(): SubmissionLedgerDao

    companion object {
        @Volatile private var instance: SubmissionLedgerDatabase? = null

        fun get(context: android.content.Context): SubmissionLedgerDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(context.applicationContext, SubmissionLedgerDatabase::class.java, "watch_submission_ledger.db")
                .build().also { instance = it }
        }
    }
}

class RoomSubmissionLedger(context: android.content.Context) : SubmissionLedger {
    private val dao = SubmissionLedgerDatabase.get(context).ledger()
    private val preferences = context.applicationContext.getSharedPreferences(LEGACY_LEDGER, Context.MODE_PRIVATE)

    override suspend fun entry(submissionId: UUID): SubmissionLedgerEntry? {
        migrateLegacy()
        return dao.row(submissionId.toString())?.toEntry()
    }

    override suspend fun createPending(submission: TransactionSubmission, transactionId: String): SubmissionLedgerEntry {
        migrateLegacy()
        return dao.getOrCreate(
            SubmissionLedgerRow(
                submissionId = submission.submissionId.toString(),
                transactionId = transactionId,
                outcome = SubmissionOutcome.Pending.name,
                payload = null,
                code = null,
                message = null,
            ),
        ).toEntry()
    }

    override suspend fun finish(submissionId: UUID, outcome: SubmissionOutcome, code: String?, message: String?) {
        migrateLegacy()
        dao.finish(submissionId.toString(), outcome.name, code, message)
    }

    private suspend fun migrateLegacy() = migrationMutex.withLock {
        val entries = preferences.getStringSet(LEGACY_ENTRIES, null)?.toSet() ?: return@withLock
        for (row in legacyLedgerRows(entries)) dao.insert(row)
        preferences.edit().remove(LEGACY_ENTRIES).commit()
    }

    private companion object {
        const val LEGACY_LEDGER = "watch_submission_ledger"
        const val LEGACY_ENTRIES = "entries"
        val migrationMutex = Mutex()
    }
}

class PhoneTransactionIntake(
    private val store: FinanceDirectoryStore,
    private val ledger: SubmissionLedger = InMemorySubmissionLedger(),
) {
    private val mutex = Mutex()

    suspend fun intake(submission: TransactionSubmission): TransactionAcknowledgement? = mutex.withLock {
        val existing = ledger.entry(submission.submissionId)
        when (existing?.outcome) {
            SubmissionOutcome.Accepted, SubmissionOutcome.Duplicate -> {
                return acknowledgement(submission, AcknowledgementStatus.Duplicate)
            }
            SubmissionOutcome.Rejected -> return rejected(submission, existing.message ?: "Rejected.", existing.code ?: "invalid_submission")
            SubmissionOutcome.Pending, null -> Unit
        }
        val entry = existing ?: ledger.createPending(submission, UUID.randomUUID().toString())
        TransactionProtocolValidator.submissionError(submission)?.let {
            ledger.finish(submission.submissionId, SubmissionOutcome.Rejected, "invalid_submission", it)
            return rejected(submission, it)
        }
        try {
            if (store.containsTransaction(entry.transactionId)) {
                ledger.finish(submission.submissionId, SubmissionOutcome.Duplicate)
                return acknowledgement(submission, AcknowledgementStatus.Duplicate)
            }
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
                transactionId = entry.transactionId,
                allowUnregisteredCategory = true,
            )
            ledger.finish(submission.submissionId, SubmissionOutcome.Accepted)
            acknowledgement(submission, AcknowledgementStatus.Accepted)
        } catch (_: Throwable) {
            null
        }
    }

    private fun acknowledgement(submission: TransactionSubmission, status: AcknowledgementStatus) =
        TransactionAcknowledgement(submissionId = submission.submissionId, status = status)

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

class InMemorySubmissionLedger : SubmissionLedger {
    private val entries = mutableMapOf<UUID, SubmissionLedgerEntry>()

    override suspend fun entry(submissionId: UUID): SubmissionLedgerEntry? = entries[submissionId]

    override suspend fun createPending(submission: TransactionSubmission, transactionId: String): SubmissionLedgerEntry {
        return entries.getOrPut(submission.submissionId) {
            SubmissionLedgerEntry(
                submissionId = submission.submissionId,
                transactionId = transactionId,
                outcome = SubmissionOutcome.Pending,
                payload = null,
            )
        }
    }

    override suspend fun finish(submissionId: UUID, outcome: SubmissionOutcome, code: String?, message: String?) {
        entries[submissionId]?.let { entry ->
            entries[submissionId] = entry.copy(outcome = outcome, payload = null, code = code, message = message)
        }
    }
}

private fun SubmissionLedgerRow.toEntry() = SubmissionLedgerEntry(
    submissionId = UUID.fromString(submissionId),
    transactionId = transactionId,
    outcome = SubmissionOutcome.valueOf(outcome),
    payload = payload,
    code = code,
    message = message,
)

internal fun legacyLedgerRows(entries: Set<String>): List<SubmissionLedgerRow> = entries.sorted().mapNotNull { entry ->
    val separator = entry.indexOf('=')
    if (separator <= 0) return@mapNotNull null
    val submissionId = entry.take(separator)
    val transactionId = entry.drop(separator + 1)
    uuidFromStringOrNull(submissionId)?.takeIf { transactionId.isNotBlank() }?.let {
        SubmissionLedgerRow(
            submissionId = it.toString(),
            transactionId = transactionId,
            outcome = SubmissionOutcome.Pending.name,
            payload = null,
            code = null,
            message = null,
        )
    }
}

private fun uuidFromStringOrNull(value: String): UUID? = runCatching { UUID.fromString(value) }.getOrNull()
