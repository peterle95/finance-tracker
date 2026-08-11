package com.peterle95.financetracker

import com.google.android.gms.wearable.MessageEvent
import com.google.android.gms.wearable.Wearable
import com.peterle95.financetracker.data.FinanceRepository
import com.peterle95.financetracker.protocol.TRANSACTION_ACKNOWLEDGEMENTS_PATH
import com.peterle95.financetracker.protocol.TRANSACTION_SUBMISSIONS_PATH
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

class WearableListenerService : com.google.android.gms.wearable.WearableListenerService() {
    private val repository by lazy { FinanceRepository(applicationContext) }

    override fun onMessageReceived(messageEvent: MessageEvent) {
        if (messageEvent.path != TRANSACTION_SUBMISSIONS_PATH) return
        val submission = TransactionProtocolCodec.decodeSubmission(messageEvent.data) ?: return
        CoroutineScope(Dispatchers.IO).launch {
            val acknowledgement = repository.intakeWatchSubmission(submission)
            Wearable.getMessageClient(applicationContext).sendMessage(
                messageEvent.sourceNodeId,
                TRANSACTION_ACKNOWLEDGEMENTS_PATH,
                TransactionProtocolCodec.encodeAcknowledgement(acknowledgement),
            )
        }
    }
}
