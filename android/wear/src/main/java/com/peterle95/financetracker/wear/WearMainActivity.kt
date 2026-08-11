package com.peterle95.financetracker.wear

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.watchcapture.WatchCaptureCategories
import com.peterle95.financetracker.watchcapture.WatchCaptureInput
import com.peterle95.financetracker.watchcapture.WatchCaptureSubmission
import kotlinx.coroutines.delay
import java.time.LocalDate

class WearMainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val pending = PendingSubmissionStore(applicationContext)
        val sender = WatchSubmissionSender(applicationContext, pending)
        setContent {
            var amount by rememberSaveable { mutableStateOf("") }
            var category by rememberSaveable { mutableStateOf(WatchCaptureCategories.expense.first()) }
            var status by remember { mutableStateOf(pending.status()) }
            var hasPending by remember { mutableStateOf(pending.pending() != null) }
            MaterialTheme {
                LazyColumn(modifier = Modifier.padding(8.dp)) {
                    item { Text("Record expense") }
                    item {
                        OutlinedTextField(
                            value = amount,
                            onValueChange = { amount = it },
                            label = { Text("Amount") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    item { Text("Category: $category", modifier = Modifier.padding(top = 8.dp)) }
                    items(WatchCaptureCategories.expense) { name ->
                        Button(onClick = { category = name }, modifier = Modifier.fillMaxWidth()) { Text(name) }
                    }
                    item {
                        Button(
                            onClick = {
                                runCatching {
                                    WatchCaptureSubmission.create(
                                        WatchCaptureInput(
                                            type = SubmissionType.Expense,
                                            amountText = amount,
                                            category = category,
                                            description = "",
                                            date = LocalDate.now().toString(),
                                        ),
                                    ).also(pending::save)
                                }.onSuccess {
                                    status = "Sending expense..."
                                    hasPending = true
                                }.onFailure {
                                    status = it.message ?: "Invalid expense."
                                }
                            },
                            enabled = !hasPending,
                            modifier = Modifier.fillMaxWidth(),
                        ) { Text("Submit") }
                    }
                    item { Text(status, modifier = Modifier.padding(top = 8.dp)) }
                }
            }
            LaunchedEffect(hasPending) {
                if (!hasPending) return@LaunchedEffect
                status = runCatching { sender.sendPending() }.getOrElse { it.message ?: "Phone unavailable." }
                while (pending.pending() != null) {
                    delay(500)
                    status = pending.status()
                }
                hasPending = false
            }
        }
    }
}
