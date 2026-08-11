package com.peterle95.financetracker.wear

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Button
import androidx.compose.material3.Checkbox
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.watchcapture.WatchCaptureForm
import com.peterle95.financetracker.watchcapture.WatchCaptureFormLogic
import com.peterle95.financetracker.watchcapture.WatchCaptureInput
import com.peterle95.financetracker.watchcapture.WatchCaptureSubmission
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch
import java.time.LocalDate

class WearMainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val outbox = WatchOutbox(applicationContext)
        val snapshots = WatchCategoryCache.snapshots(applicationContext)
        WatchDeliveryScheduler.schedule(applicationContext)
        deliveryScope.launch { runCatching { WatchCategoryCache.refresh(applicationContext) } }
        setContent {
            val snapshot by snapshots.collectAsState()
            var typeName by rememberSaveable { mutableStateOf(SubmissionType.Expense.name) }
            var amount by rememberSaveable { mutableStateOf("") }
            var category by rememberSaveable { mutableStateOf(snapshot.expenseCategories.firstOrNull().orEmpty()) }
            var description by rememberSaveable { mutableStateOf("") }
            var date by rememberSaveable { mutableStateOf(LocalDate.now().toString()) }
            var isBnpl by rememberSaveable { mutableStateOf(true) }
            var status by remember { mutableStateOf("Ready") }
            var saving by remember { mutableStateOf(false) }
            val type = SubmissionType.valueOf(typeName)
            val form = WatchCaptureForm(type, amount, category, description, date, isBnpl)
            val categories = WatchCaptureFormLogic.categories(form, snapshot)
            val amountError = WatchCaptureFormLogic.amountError(amount)
            val categoryError = WatchCaptureFormLogic.categoryError(category)
            val dateError = WatchCaptureFormLogic.dateError(date)
            MaterialTheme {
                LazyColumn(modifier = Modifier.padding(8.dp)) {
                    item { Text("Record transaction") }
                    item {
                        OutlinedTextField(
                            value = amount,
                            onValueChange = { amount = it },
                            label = { Text("Amount") },
                            isError = amount.isNotBlank() && amountError != null,
                            supportingText = {
                                if (amount.isNotBlank()) amountError?.let { Text(it) }
                            },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    item { Text("Category: ${category.ifBlank { "None available" }}", modifier = Modifier.padding(top = 8.dp)) }
                    if (categoryError != null) {
                        item { Text(categoryError, color = MaterialTheme.colorScheme.error) }
                    }
                    items(categories) { name ->
                        Button(onClick = { category = name }, modifier = Modifier.fillMaxWidth()) { Text(name) }
                    }
                    item {
                        Button(
                            onClick = {
                                if (saving) return@Button
                                saving = true
                                runCatching {
                                    WatchCaptureSubmission.create(
                                        WatchCaptureInput(type, amount, category, description, date, isBnpl),
                                    )
                                }.onSuccess { submission ->
                                    deliveryScope.launch {
                                        runCatching {
                                            outbox.save(submission)
                                            WatchDeliveryScheduler.schedule(applicationContext)
                                        }.onSuccess {
                                            runOnUiThread {
                                                if (!isDestroyed) {
                                                    status = "Sending transaction..."
                                                    saving = false
                                                }
                                            }
                                        }.onFailure {
                                            runOnUiThread {
                                                if (!isDestroyed) {
                                                    status = it.message ?: "Could not save transaction."
                                                    saving = false
                                                }
                                            }
                                        }
                                    }
                                }.onFailure {
                                    status = it.message ?: "Invalid transaction."
                                    saving = false
                                }
                            },
                            enabled = !saving && WatchCaptureFormLogic.canSubmit(form),
                            modifier = Modifier.fillMaxWidth(),
                        ) { Text("Add") }
                    }
                    item {
                        OutlinedTextField(
                            value = description,
                            onValueChange = { description = it },
                            label = { Text("Description (optional)") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    item {
                        OutlinedTextField(
                            value = date,
                            onValueChange = { date = it },
                            label = { Text("Date (YYYY-MM-DD)") },
                            isError = dateError != null,
                            supportingText = { dateError?.let { Text(it) } },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    item {
                        Text("Type: ${type.name}")
                        Row {
                            SubmissionType.entries.forEach { choice ->
                                Button(onClick = {
                                    val changed = WatchCaptureFormLogic.switchType(form, choice, snapshot)
                                    typeName = changed.type.name
                                    category = changed.category
                                    isBnpl = changed.isBnpl
                                }) { Text(choice.name) }
                            }
                        }
                    }
                    if (type == SubmissionType.Expense) {
                        item {
                            Row {
                                Checkbox(checked = isBnpl, onCheckedChange = { isBnpl = it })
                                Text("Buy now, pay later", modifier = Modifier.padding(top = 12.dp))
                            }
                        }
                    }
                    item { Text(status, modifier = Modifier.padding(top = 8.dp)) }
                }
            }
            LaunchedEffect(typeName, snapshot.revision) {
                category = WatchCaptureFormLogic.refreshCategory(form, snapshot).category
            }
            LaunchedEffect(Unit) {
                outbox.status().collect { status = it }
            }
        }
    }
}

private val deliveryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
