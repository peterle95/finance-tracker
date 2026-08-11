package com.peterle95.financetracker.wear

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
import androidx.work.BackoffPolicy
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.CapabilityClient
import com.google.android.gms.wearable.Wearable
import com.google.android.gms.wearable.DataEventBuffer
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.TRANSACTION_ACKNOWLEDGEMENTS_PATH
import com.peterle95.financetracker.protocol.TRANSACTION_SUBMISSIONS_PATH
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import com.peterle95.financetracker.protocol.TransactionSubmission
import com.peterle95.financetracker.watchcapture.WatchCaptureFormLogic
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

private const val PHONE_CAPABILITY = "finance_phone"

@Entity(tableName = "watch_submission_outbox")
data class WatchOutboxRow(
    @androidx.room.PrimaryKey val submissionId: String,
    val payload: String?,
    val state: String = PENDING,
    val message: String? = null,
)

@Dao
abstract class WatchOutboxDao {
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    abstract suspend fun insert(row: WatchOutboxRow): Long

    @Query("SELECT * FROM watch_submission_outbox WHERE submissionId = :submissionId")
    abstract suspend fun row(submissionId: String): WatchOutboxRow?

    @Query("SELECT * FROM watch_submission_outbox WHERE state = :state ORDER BY rowid")
    abstract suspend fun rows(state: String): List<WatchOutboxRow>

    @Query("SELECT EXISTS(SELECT 1 FROM watch_submission_outbox WHERE state = :state)")
    abstract suspend fun hasRows(state: String): Boolean

    @Query("SELECT * FROM watch_submission_outbox WHERE state = :state ORDER BY rowid")
    abstract fun rowsFlow(state: String): Flow<List<WatchOutboxRow>>

    @Query("SELECT * FROM watch_submission_outbox WHERE state = :state ORDER BY rowid DESC LIMIT 1")
    abstract fun latestRowFlow(state: String): Flow<WatchOutboxRow?>

    @Query("UPDATE watch_submission_outbox SET state = :state, message = :message WHERE submissionId = :submissionId")
    abstract suspend fun reject(submissionId: String, state: String, message: String?): Int

    @Query("DELETE FROM watch_submission_outbox WHERE submissionId = :submissionId")
    abstract suspend fun delete(submissionId: String): Int

    @Query("DELETE FROM watch_submission_outbox WHERE submissionId = :submissionId AND state = :state")
    abstract suspend fun delete(submissionId: String, state: String): Int

    @Transaction
    open suspend fun replaceRejected(oldSubmissionId: String, row: WatchOutboxRow): Boolean {
        if (this.row(oldSubmissionId)?.state != REJECTED) return false
        if (delete(oldSubmissionId, REJECTED) != 1) return false
        require(insert(row) != -1L) { "Correction submission ID already exists." }
        return true
    }
}

@Database(entities = [WatchOutboxRow::class], version = 1, exportSchema = false)
abstract class WatchOutboxDatabase : RoomDatabase() {
    abstract fun outbox(): WatchOutboxDao

    companion object {
        @Volatile private var instance: WatchOutboxDatabase? = null

        fun get(context: Context): WatchOutboxDatabase = instance ?: synchronized(this) {
            instance ?: Room.databaseBuilder(context.applicationContext, WatchOutboxDatabase::class.java, "watch_submission_outbox.db")
                .build().also { instance = it }
        }
    }
}

class WatchOutbox(context: Context) {
    private val dao = WatchOutboxDatabase.get(context).outbox()
    private val preferences = context.applicationContext.getSharedPreferences(LEGACY_DELIVERY, Context.MODE_PRIVATE)

    suspend fun save(submission: TransactionSubmission) {
        migrateLegacy()
        setStatus("Sending transaction...")
        dao.insert(WatchOutboxRow(submission.submissionId.toString(), TransactionProtocolCodec.encodeSubmission(submission).decodeToString()))
    }

    suspend fun replaceRejected(rejectedSubmissionId: String, submission: TransactionSubmission): Boolean {
        migrateLegacy()
        val replaced = dao.replaceRejected(
            rejectedSubmissionId,
            WatchOutboxRow(submission.submissionId.toString(), TransactionProtocolCodec.encodeSubmission(submission).decodeToString()),
        )
        if (replaced) setStatus("Sending transaction...")
        return replaced
    }

    suspend fun pending(): List<TransactionSubmission> {
        migrateLegacy()
        return dao.rows(PENDING).mapNotNull { row ->
            row.payload?.encodeToByteArray()?.let(TransactionProtocolCodec::decodeSubmission)
        }
    }

    suspend fun hasPending(): Boolean {
        migrateLegacy()
        return dao.hasRows(PENDING)
    }

    fun status(): Flow<String> = flow {
        migrateLegacy()
        emitAll(dao.rowsFlow(PENDING).map { pending ->
            if (pending.isNotEmpty()) "Sending transaction..." else preferences.getString(STATUS, "Ready") ?: "Ready"
        })
    }

    fun outcomes(recoverySubmissionId: String?): Flow<TransactionAcknowledgement> = flow {
        val recovered = preferences.getString(OUTCOME, null)?.encodeToByteArray()
            ?.let(TransactionProtocolCodec::decodeAcknowledgement)
            ?.takeIf { it.submissionId.toString() == recoverySubmissionId }
        if (recovered != null) {
            preferences.edit().remove(OUTCOME).commit()
            emit(recovered)
        }
        emitAll(outcomeQueue.outcomes())
    }

    fun outcomeObserved(outcome: TransactionAcknowledgement) {
        val persistedId = preferences.getString(OUTCOME, null)?.encodeToByteArray()
            ?.let(TransactionProtocolCodec::decodeAcknowledgement)?.submissionId
        if (persistedId == outcome.submissionId) preferences.edit().remove(OUTCOME).apply()
    }

    fun latestRejected(): Flow<WatchOutboxRow?> = dao.latestRowFlow(REJECTED)

    suspend fun acknowledge(payload: ByteArray) {
        migrateLegacy()
        val acknowledgement = TransactionProtocolCodec.decodeAcknowledgement(payload) ?: return
        val changed = transitionAcknowledgementRow(
            acknowledgement,
            row = { dao.row(it) },
            delete = { dao.delete(it) == 1 },
            reject = { id, message -> dao.reject(id, REJECTED, message) == 1 },
        )
        if (!changed) return
        val status = when (acknowledgement.status) {
            AcknowledgementStatus.Accepted -> {
                "Accepted"
            }
            AcknowledgementStatus.Duplicate -> {
                "Already accepted"
            }
            AcknowledgementStatus.Rejected -> {
                WatchCaptureFormLogic.rejectionText(acknowledgement.code, acknowledgement.message)
            }
        }
        preferences.edit()
            .putString(STATUS, status)
            .putString(OUTCOME, TransactionProtocolCodec.encodeAcknowledgement(acknowledgement).decodeToString())
            .commit()
        outcomeQueue.send(acknowledgement)
    }

    private suspend fun migrateLegacy() = migrationMutex.withLock {
        val payload = preferences.getString(PENDING_SUBMISSION, null)
        val legacyStatus = preferences.getString(LEGACY_STATUS, null)
        if (payload == null && legacyStatus == null) return@withLock
        payload?.let {
            TransactionProtocolCodec.decodeSubmission(it.encodeToByteArray())?.let { submission ->
                dao.insert(WatchOutboxRow(submission.submissionId.toString(), it))
            }
        }
        preferences.edit().apply {
            legacyStatus?.let { putString(STATUS, it) }
            remove(PENDING_SUBMISSION)
            remove(LEGACY_STATUS)
        }.commit()
    }

    private fun setStatus(status: String) {
        preferences.edit().putString(STATUS, status).apply()
    }

    private companion object {
        const val LEGACY_DELIVERY = "watch_delivery"
        const val PENDING_SUBMISSION = "pending_submission"
        const val LEGACY_STATUS = "status"
        const val STATUS = "delivery_status"
        const val OUTCOME = "delivery_outcome"
        val migrationMutex = Mutex()
        val outcomeQueue = WatchOutcomeQueue()
    }
}

internal class WatchOutcomeQueue {
    private val channel = Channel<TransactionAcknowledgement>(Channel.UNLIMITED)

    fun outcomes(): Flow<TransactionAcknowledgement> = channel.receiveAsFlow()

    fun send(outcome: TransactionAcknowledgement) {
        check(channel.trySend(outcome).isSuccess)
    }
}

class WatchSubmissionSender(private val context: Context, private val outbox: WatchOutbox) {
    suspend fun sendPending(): Boolean = withContext(Dispatchers.IO) {
        val submissions = outbox.pending()
        if (submissions.isEmpty()) return@withContext true
        val capability = Tasks.await(
            Wearable.getCapabilityClient(context).getCapability(PHONE_CAPABILITY, CapabilityClient.FILTER_REACHABLE),
            DELIVERY_TIMEOUT_SECONDS,
            TimeUnit.SECONDS,
        )
        val node = capability.nodes.firstOrNull() ?: return@withContext false
        submissions.forEach { submission ->
            Tasks.await(
                Wearable.getMessageClient(context).sendMessage(
                    node.id,
                    TRANSACTION_SUBMISSIONS_PATH,
                    TransactionProtocolCodec.encodeSubmission(submission),
                ),
                DELIVERY_TIMEOUT_SECONDS,
                TimeUnit.SECONDS,
            )
        }
        true
    }
}

object WatchDeliveryScheduler {
    fun schedule(context: Context) {
        val request = OneTimeWorkRequestBuilder<WatchSubmissionWorker>()
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.NOT_REQUIRED).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 10, TimeUnit.SECONDS)
            .build()
        WorkManager.getInstance(context).enqueueUniqueWork(DELIVERY_WORK, ExistingWorkPolicy.REPLACE, request)
    }
}

class WatchSubmissionWorker(context: Context, parameters: WorkerParameters) : CoroutineWorker(context, parameters) {
    override suspend fun doWork(): Result = runCatching {
        val outbox = WatchOutbox(applicationContext)
        if (!outbox.hasPending()) {
            deliveryResult(DeliveryAttempt.NotNeeded, hasPending = false).toWorkerResult()
        } else {
            val sent = WatchSubmissionSender(applicationContext, outbox).sendPending()
            deliveryResult(
                if (sent) DeliveryAttempt.Succeeded else DeliveryAttempt.Failed,
                hasPending = outbox.hasPending(),
            ).toWorkerResult()
        }
    }.getOrElse { Result.retry() }

    private fun DeliveryResult.toWorkerResult() = when (this) {
        DeliveryResult.Success -> Result.success()
        DeliveryResult.Retry -> Result.retry()
    }
}

internal enum class DeliveryAttempt { NotNeeded, Failed, Succeeded }
internal enum class DeliveryResult { Success, Retry }

internal suspend fun transitionAcknowledgementRow(
    acknowledgement: TransactionAcknowledgement,
    row: suspend (String) -> WatchOutboxRow?,
    delete: suspend (String) -> Boolean,
    reject: suspend (String, String) -> Boolean,
): Boolean {
    val id = acknowledgement.submissionId.toString()
    if (row(id) == null) return false
    return when (acknowledgement.status) {
        AcknowledgementStatus.Accepted, AcknowledgementStatus.Duplicate -> delete(id)
        AcknowledgementStatus.Rejected -> reject(
            id,
            WatchCaptureFormLogic.rejectionText(acknowledgement.code, acknowledgement.message),
        )
    }
}

internal fun deliveryResult(attempt: DeliveryAttempt, hasPending: Boolean) =
    if (attempt != DeliveryAttempt.Failed && !hasPending) DeliveryResult.Success else DeliveryResult.Retry

class WearAcknowledgementListenerService : com.google.android.gms.wearable.WearableListenerService() {
    override fun onMessageReceived(messageEvent: com.google.android.gms.wearable.MessageEvent) {
        if (messageEvent.path == TRANSACTION_ACKNOWLEDGEMENTS_PATH) {
            runBlocking(Dispatchers.IO) {
                WatchOutbox(applicationContext).acknowledge(messageEvent.data)
            }
        }
    }

    override fun onDataChanged(dataEvents: DataEventBuffer) {
        if (WatchCategoryCache.accept(applicationContext, dataEvents)) {
            categoryRefreshScope.launch { runCatching { WatchCategoryCache.refresh(applicationContext) } }
        }
    }

    private companion object {
        private val categoryRefreshScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    }
}

private const val PENDING = "pending"
private const val REJECTED = "rejected"
private const val DELIVERY_WORK = "watch_submission_delivery"
private const val DELIVERY_TIMEOUT_SECONDS = 20L
