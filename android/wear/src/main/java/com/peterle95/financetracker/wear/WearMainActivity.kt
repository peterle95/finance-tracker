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
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.SubmissionType
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
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
            var activeSubmission by rememberSaveable(stateSaver = ActiveSubmissionSaver) { mutableStateOf(ActiveSubmission()) }
            var rejectedSubmissionId by rememberSaveable { mutableStateOf<String?>(null) }
            var categoryLocked by rememberSaveable { mutableStateOf(false) }
            var formTouched by rememberSaveable { mutableStateOf(false) }
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
                            onValueChange = { amount = it; formTouched = true },
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
                        Button(onClick = { category = name; formTouched = true }, modifier = Modifier.fillMaxWidth()) { Text(name) }
                    }
                    item {
                        Button(
                            onClick = {
                                if (saving) return@Button
                                saving = true
                                runCatching {
                                    val input = WatchCaptureInput(type, amount, category, description, date, isBnpl)
                                    rejectedSubmissionId?.let { WatchCaptureSubmission.correct(input, java.util.UUID.fromString(it)) }
                                        ?: WatchCaptureSubmission.create(input)
                                }.onSuccess { submission ->
                                    val correctionId = rejectedSubmissionId
                                    activeSubmission = ActiveSubmission(submission.submissionId.toString(), form)
                                    categoryLocked = true
                                    deliveryScope.launch {
                                        runCatching {
                                            if (correctionId == null) outbox.save(submission)
                                            else if (!outbox.replaceRejected(correctionId, submission)) outbox.save(submission)
                                            WatchDeliveryScheduler.schedule(applicationContext)
                                        }.onSuccess {
                                            runOnUiThread {
                                                if (!isDestroyed) {
                                                    status = "Sending transaction..."
                                                    rejectedSubmissionId = null
                                                    saving = false
                                                }
                                            }
                                        }.onFailure {
                                            runOnUiThread {
                                                if (!isDestroyed) {
                                                    status = it.message ?: "Could not save transaction."
                                                    activeSubmission = ActiveSubmission()
                                                    rejectedSubmissionId = null
                                                    categoryLocked = false
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
                            onValueChange = { description = it; formTouched = true },
                            label = { Text("Description (optional)") },
                            modifier = Modifier.fillMaxWidth(),
                        )
                    }
                    item {
                        OutlinedTextField(
                            value = date,
                            onValueChange = { date = it; formTouched = true },
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
                                    categoryLocked = false
                                    formTouched = true
                                }) { Text(choice.name) }
                            }
                        }
                    }
                    if (type == SubmissionType.Expense) {
                        item {
                            Row {
                                Checkbox(checked = isBnpl, onCheckedChange = { isBnpl = it; formTouched = true })
                                Text("Buy now, pay later", modifier = Modifier.padding(top = 12.dp))
                            }
                        }
                    }
                    item { Text(status, modifier = Modifier.padding(top = 8.dp)) }
                }
            }
            LaunchedEffect(typeName, snapshot.revision) {
                if (!categoryLocked) category = WatchCaptureFormLogic.refreshCategory(form, snapshot).category
            }
            LaunchedEffect(Unit) {
                outbox.pending().lastOrNull()?.takeIf { activeSubmission.id == null }?.let { submission ->
                    activeSubmission = ActiveSubmission(
                        submission.submissionId.toString(),
                        WatchCaptureForm(
                            submission.type,
                            submission.amount.toString(),
                            submission.category,
                            submission.description,
                            submission.transactionDate,
                            submission.isBnpl,
                        ),
                    )
                }
                outbox.status().collect { status = it }
            }
            LaunchedEffect(Unit) {
                outbox.latestRejected().collect { row ->
                    if (row == null) {
                        rejectedSubmissionId = null
                        if (activeSubmission.id == null) categoryLocked = false
                        return@collect
                    }
                    if (WatchCaptureFormLogic.shouldRestoreRejected(activeSubmission.id, formTouched) &&
                        rejectedSubmissionId != row.submissionId
                    ) {
                        val submission = row.payload?.encodeToByteArray()?.let(TransactionProtocolCodec::decodeSubmission)
                            ?: return@collect
                        typeName = submission.type.name
                        amount = submission.amount.toString()
                        category = submission.category
                        description = submission.description
                        date = submission.transactionDate
                        isBnpl = submission.isBnpl
                        rejectedSubmissionId = row.submissionId
                        categoryLocked = true
                        formTouched = false
                    }
                }
            }
            LaunchedEffect(activeSubmission.id) {
                outbox.outcomes(activeSubmission.id).collect { outcome ->
                    if (outcome.submissionId.toString() != activeSubmission.id) return@collect
                    val currentForm = WatchCaptureForm(SubmissionType.valueOf(typeName), amount, category, description, date, isBnpl)
                    val unchanged = WatchCaptureFormLogic.shouldApplyOutcome(currentForm, activeSubmission.form ?: return@collect)
                    val reset = unchanged && outcome.status == AcknowledgementStatus.Accepted
                    val changed = if (unchanged) {
                        WatchCaptureFormLogic.applyOutcome(currentForm, outcome, snapshot)
                    } else {
                        currentForm
                    }
                    typeName = changed.type.name
                    amount = changed.amountText
                    category = changed.category
                    description = changed.description
                    date = changed.date
                    isBnpl = changed.isBnpl
                    outbox.outcomeObserved(outcome)
                    activeSubmission = ActiveSubmission()
                    if (reset) formTouched = false
                    categoryLocked = !reset
                    rejectedSubmissionId = outcome.submissionId.toString().takeIf {
                        outcome.status == AcknowledgementStatus.Rejected
                    }
                    status = when (outcome.status) {
                        AcknowledgementStatus.Accepted -> "Accepted"
                        AcknowledgementStatus.Duplicate -> "Already accepted"
                        AcknowledgementStatus.Rejected -> WatchCaptureFormLogic.rejectionText(outcome.code, outcome.message)
                    }
                }
            }
        }
    }
}

private val deliveryScope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

private data class ActiveSubmission(val id: String? = null, val form: WatchCaptureForm? = null)

private val ActiveSubmissionSaver = listSaver<ActiveSubmission, Any>(
    save = { active ->
        active.form?.let { form ->
            listOf(active.id.orEmpty(), form.type.name, form.amountText, form.category, form.description, form.date, form.isBnpl)
        } ?: emptyList()
    },
    restore = { saved ->
        if (saved.isEmpty()) ActiveSubmission()
        else ActiveSubmission(
            saved[0] as String,
            WatchCaptureForm(
                SubmissionType.valueOf(saved[1] as String),
                saved[2] as String,
                saved[3] as String,
                saved[4] as String,
                saved[5] as String,
                saved[6] as Boolean,
            ),
        )
    },
)
