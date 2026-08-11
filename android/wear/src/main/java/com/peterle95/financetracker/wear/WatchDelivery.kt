package com.peterle95.financetracker.wear

import android.content.Context
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.CapabilityClient
import com.google.android.gms.wearable.Wearable
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.TRANSACTION_ACKNOWLEDGEMENTS_PATH
import com.peterle95.financetracker.protocol.TRANSACTION_SUBMISSIONS_PATH
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import com.peterle95.financetracker.protocol.TransactionSubmission
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

private const val PHONE_CAPABILITY = "finance_phone"

class PendingSubmissionStore(context: Context) {
    private val preferences = context.getSharedPreferences("watch_delivery", Context.MODE_PRIVATE)

    fun save(submission: TransactionSubmission) {
        preferences.edit().putString(PENDING_SUBMISSION, TransactionProtocolCodec.encodeSubmission(submission).decodeToString()).commit()
    }

    fun pending(): TransactionSubmission? = preferences.getString(PENDING_SUBMISSION, null)
        ?.encodeToByteArray()
        ?.let(TransactionProtocolCodec::decodeSubmission)

    fun status(): String = preferences.getString(STATUS, "Ready") ?: "Ready"

    fun acknowledge(payload: ByteArray) {
        val acknowledgement = TransactionProtocolCodec.decodeAcknowledgement(payload) ?: return
        if (acknowledgement.submissionId != pending()?.submissionId) return
        val status = when (acknowledgement.status) {
            AcknowledgementStatus.Accepted -> "Accepted"
            AcknowledgementStatus.Duplicate -> "Already accepted"
            AcknowledgementStatus.Rejected -> acknowledgement.message ?: "Rejected"
        }
        preferences.edit().apply {
            putString(STATUS, status)
            if (acknowledgement.status != AcknowledgementStatus.Rejected) remove(PENDING_SUBMISSION)
            apply()
        }
    }

    private companion object {
        const val PENDING_SUBMISSION = "pending_submission"
        const val STATUS = "status"
    }
}

class WatchSubmissionSender(
    private val context: Context,
    private val pending: PendingSubmissionStore,
) {
    suspend fun sendPending(): String = withContext(Dispatchers.IO) {
        val submission = pending.pending() ?: return@withContext "No pending expense."
        val capability = Tasks.await(
            Wearable.getCapabilityClient(context).getCapability(PHONE_CAPABILITY, CapabilityClient.FILTER_REACHABLE),
        )
        val node = capability.nodes.firstOrNull() ?: return@withContext "Phone unavailable."
        Tasks.await(
            Wearable.getMessageClient(context).sendMessage(
                node.id,
                TRANSACTION_SUBMISSIONS_PATH,
                TransactionProtocolCodec.encodeSubmission(submission),
            ),
        )
        "Sent; waiting for phone acknowledgement."
    }
}

class WearAcknowledgementListenerService : com.google.android.gms.wearable.WearableListenerService() {
    override fun onMessageReceived(messageEvent: com.google.android.gms.wearable.MessageEvent) {
        if (messageEvent.path == TRANSACTION_ACKNOWLEDGEMENTS_PATH) {
            PendingSubmissionStore(applicationContext).acknowledge(messageEvent.data)
        }
    }
}
