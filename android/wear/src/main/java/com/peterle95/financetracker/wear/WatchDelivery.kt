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
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import com.peterle95.financetracker.protocol.TransactionSubmission
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
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
    abstract suspend fun insert(row: WatchOutboxRow)

    @Query("SELECT * FROM watch_submission_outbox WHERE state = :state ORDER BY rowid")
    abstract suspend fun rows(state: String): List<WatchOutboxRow>

    @Query("SELECT EXISTS(SELECT 1 FROM watch_submission_outbox WHERE state = :state)")
    abstract suspend fun hasRows(state: String): Boolean

    @Query("SELECT * FROM watch_submission_outbox WHERE state = :state ORDER BY rowid")
    abstract fun rowsFlow(state: String): Flow<List<WatchOutboxRow>>

    @Query("UPDATE watch_submission_outbox SET state = :state, message = :message WHERE submissionId = :submissionId")
    abstract suspend fun reject(submissionId: String, state: String, message: String?)

    @Query("UPDATE watch_submission_outbox SET state = :state, payload = NULL, message = NULL WHERE submissionId = :submissionId")
    abstract suspend fun complete(submissionId: String, state: String)
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

    suspend fun acknowledge(payload: ByteArray) {
        migrateLegacy()
        val acknowledgement = TransactionProtocolCodec.decodeAcknowledgement(payload) ?: return
        when (acknowledgement.status) {
            AcknowledgementStatus.Accepted -> {
                setStatus("Accepted")
                dao.complete(acknowledgement.submissionId.toString(), ACCEPTED)
            }
            AcknowledgementStatus.Duplicate -> {
                setStatus("Already accepted")
                dao.complete(acknowledgement.submissionId.toString(), DUPLICATE)
            }
            AcknowledgementStatus.Rejected -> {
                setStatus(acknowledgement.message ?: "Rejected")
                dao.reject(acknowledgement.submissionId.toString(), REJECTED, acknowledgement.message)
            }
        }
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
        val migrationMutex = Mutex()
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
private const val ACCEPTED = "accepted"
private const val DUPLICATE = "duplicate"
private const val DELIVERY_WORK = "watch_submission_delivery"
private const val DELIVERY_TIMEOUT_SECONDS = 20L
