package com.peterle95.financetracker.data

import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.provider.DocumentsContract
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.FixedCost
import com.peterle95.financetracker.domain.IncomeSource
import com.peterle95.financetracker.domain.Loan
import com.peterle95.financetracker.domain.SavingsGoal
import com.peterle95.financetracker.domain.TransactionType
import com.peterle95.financetracker.protocol.AcknowledgementStatus
import com.peterle95.financetracker.protocol.TransactionAcknowledgement
import com.peterle95.financetracker.protocol.TransactionSubmission
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.JsonObject
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

class FinanceRepository(context: Context) {
    private val appContext = context.applicationContext
    private val contentResolver = appContext.contentResolver
    private val settingsDataStore = SettingsDataStore(appContext)
    private val mutex = sharedMutex
    private val document = MutableStateFlow(FinanceDocument.empty())
    private val _syncStatus = MutableStateFlow(SyncedFileStatus())
    private var store: FinanceDirectoryStore? = null
    private var watchIntake: PhoneTransactionIntake? = null
    private val watchLedger = SharedPreferencesSubmissionLedger(appContext)

    val transactions: Flow<List<FinanceTransaction>> = document.map { it.transactions }
    val categories: Flow<CategoryState> = document.map { it.categories }
    val budgetSettings: Flow<JsonObject> = document.map { it.budgetSettings }
    val budgetSettingsModel: Flow<BudgetSettings> = document.map { it.budgetSettingsModel }
    val syncStatus: Flow<SyncedFileStatus> = _syncStatus

    suspend fun loadConfiguredFileIfAny() {
        val uri = configuredTreeUriOrNull()
        if (uri == null) {
            _syncStatus.value = SyncedFileStatus(
                lastError = if (settingsDataStore.legacySyncedFileUri.first() != null) {
                    "Reconnect the synced directory. The previous single-file permission cannot safely access its parent."
                } else {
                    null
                },
            )
            return
        }
        reloadConnectedFile()
    }

    suspend fun connectSyncedDirectory(uri: Uri) = mutex.withLock {
        require(uri.scheme == ContentResolver.SCHEME_CONTENT && DocumentsContract.isTreeUri(uri)) {
            "Choose the synced finance data directory through Android's directory picker."
        }
        val flags = Intent.FLAG_GRANT_READ_URI_PERMISSION or Intent.FLAG_GRANT_WRITE_URI_PERMISSION
        contentResolver.takePersistableUriPermission(uri, flags)
        val candidate = FinanceDirectoryStore(SafFinanceDirectory(contentResolver, uri))
        runCatching { candidate.reload() }.onSuccess { result ->
            settingsDataStore.setSyncedTreeUri(uri.toString())
            store = candidate
            watchIntake = null
            document.value = result.document
            _syncStatus.value = SyncedFileStatus(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastLoadedAt = nowText(),
                lastWrittenAt = if (result.migratedLegacy) nowText() else null,
                warnings = result.warnings,
            )
        }.onFailure { error ->
            _syncStatus.value = _syncStatus.value.copy(lastError = error.message ?: "Could not connect directory.")
            throw error
        }
    }

    suspend fun reloadConnectedFile() = mutex.withLock {
        val uri = requireConfiguredTreeUri()
        val activeStore = FinanceDirectoryStore(SafFinanceDirectory(contentResolver, uri))
        runCatching { activeStore.reload() }.onSuccess { result ->
            store = activeStore
            watchIntake = null
            document.value = result.document
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastLoadedAt = nowText(),
                lastWrittenAt = if (result.migratedLegacy) nowText() else _syncStatus.value.lastWrittenAt,
                lastError = null,
                warnings = result.warnings,
            )
        }.onFailure { error ->
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastError = error.message ?: "Could not reload synced directory.",
            )
            throw error
        }
    }

    suspend fun addTransaction(
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        behaviorDate: String? = null,
    ) = mutate {
        it.addTransaction(type, date, amount, category, description, behaviorDate)
    }

    suspend fun deleteTransaction(exportId: String) = mutate { it.deleteTransaction(exportId) }

    suspend fun updateTransaction(
        exportId: String,
        type: TransactionType,
        date: String,
        amount: Double,
        category: String,
        description: String,
        behaviorDate: String?,
    ) = mutate {
        it.updateTransaction(exportId, type, date, amount, category, description, behaviorDate)
    }

    suspend fun setCategories(type: TransactionType, categories: List<String>) = mutate {
        it.setCategories(type, categories)
    }

    suspend fun intakeWatchSubmission(submission: TransactionSubmission): TransactionAcknowledgement = mutex.withLock {
        try {
            val uri = requireConfiguredTreeUri()
            val activeStore = store ?: FinanceDirectoryStore(SafFinanceDirectory(contentResolver, uri)).also {
                it.reload()
                store = it
            }
            val acknowledgement = (watchIntake ?: PhoneTransactionIntake(activeStore, watchLedger).also { watchIntake = it })
                .intake(submission)
            document.value = activeStore.document.value
            if (acknowledgement.status != AcknowledgementStatus.Rejected) {
                _syncStatus.value = _syncStatus.value.copy(
                    uri = uri.toString(),
                    fileName = displayName(uri),
                    lastLoadedAt = nowText(),
                    lastWrittenAt = if (acknowledgement.status == AcknowledgementStatus.Accepted) nowText() else _syncStatus.value.lastWrittenAt,
                    lastError = null,
                    warnings = activeStore.warnings(),
                )
            }
            acknowledgement
        } catch (error: Throwable) {
            TransactionAcknowledgement(
                submissionId = submission.submissionId,
                status = AcknowledgementStatus.Rejected,
                code = "write_failed",
                message = error.message ?: "Could not write transaction.",
            )
        }
    }

    suspend fun updateBalances(bank: Double, wallet: Double, savings: Double, investments: Double) =
        mutateOwner(FileOwner.NetWorth) { latest ->
            FinanceJsonCodec.updateBalances(
                latest,
                latest.budgetSettingsModel.balances.copy(
                    bankAccount = bank,
                    wallet = wallet,
                    savings = savings,
                    investments = investments,
                    hasAnyBalanceField = true,
                ),
            )
        }

    suspend fun setDailySavingsGoal(amount: Double) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.setDailySavingsGoal(it, amount)
    }

    suspend fun addIncomeSource(source: IncomeSource) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.addIncomeSource(it, source)
    }

    suspend fun updateIncomeSource(key: String, source: IncomeSource) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.updateIncomeSource(it, key, source)
    }

    suspend fun archiveIncomeSource(key: String, endDate: String) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.archiveIncomeSource(it, key, endDate)
    }

    suspend fun deleteIncomeSource(key: String) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.deleteIncomeSource(it, key)
    }

    suspend fun addFixedCost(cost: FixedCost) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.addFixedCost(it, cost)
    }

    suspend fun updateFixedCost(key: String, cost: FixedCost) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.updateFixedCost(it, key, cost)
    }

    suspend fun archiveFixedCost(key: String, endDate: String) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.archiveFixedCost(it, key, endDate)
    }

    suspend fun deleteFixedCost(key: String) = mutateOwner(FileOwner.Budget) {
        FinanceJsonCodec.deleteFixedCost(it, key)
    }

    suspend fun addLoan(loan: Loan) = mutateOwner(FileOwner.Loans) { FinanceJsonCodec.addLoan(it, loan) }
    suspend fun updateLoan(key: String, loan: Loan) = mutateOwner(FileOwner.Loans) {
        FinanceJsonCodec.updateLoan(it, key, loan)
    }
    suspend fun returnLoan(key: String) = mutateOwner(FileOwner.Loans) { FinanceJsonCodec.returnLoan(it, key) }

    suspend fun addSavingsGoal(goal: SavingsGoal) = mutateOwner(FileOwner.SavingsGoals) {
        FinanceJsonCodec.addSavingsGoal(it, goal)
    }
    suspend fun updateSavingsGoal(key: String, goal: SavingsGoal) = mutateOwner(FileOwner.SavingsGoals) {
        FinanceJsonCodec.updateSavingsGoal(it, key, goal)
    }
    suspend fun allocateSavingsGoal(key: String, amount: Double) = mutateOwner(FileOwner.SavingsGoals) {
        FinanceJsonCodec.allocateSavingsGoal(it, key, amount)
    }
    suspend fun deleteSavingsGoal(key: String) = mutateOwner(FileOwner.SavingsGoals) {
        FinanceJsonCodec.deleteSavingsGoal(it, key)
    }
    suspend fun autoDistributeSavings() = mutateOwner(FileOwner.SavingsGoals) {
        FinanceJsonCodec.autoDistributeSavings(it)
    }

    suspend fun recordAssetSnapshot(date: String, note: String) = mutateOwner(FileOwner.NetWorth) {
        FinanceJsonCodec.recordAssetSnapshot(it, date, note)
    }
    suspend fun deleteAssetSnapshot(date: String) = mutateOwner(FileOwner.NetWorth) {
        FinanceJsonCodec.deleteAssetSnapshot(it, date)
    }

    private suspend fun mutateOwner(owner: FileOwner, transform: (FinanceDocument) -> FinanceDocument) = mutate {
        it.mutateOwner(owner, transform)
    }

    private suspend fun mutate(block: suspend (FinanceDirectoryStore) -> Unit) = mutex.withLock {
        val uri = requireConfiguredTreeUri()
        val activeStore = store ?: FinanceDirectoryStore(SafFinanceDirectory(contentResolver, uri)).also { store = it }
        runCatching { block(activeStore) }.onSuccess {
            document.value = activeStore.document.value
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastLoadedAt = nowText(),
                lastWrittenAt = nowText(),
                lastError = null,
                warnings = activeStore.warnings(),
            )
        }.onFailure { error ->
            _syncStatus.value = _syncStatus.value.copy(
                uri = uri.toString(),
                fileName = displayName(uri),
                lastError = error.message ?: "Could not write synced directory.",
            )
            throw error
        }
    }

    private suspend fun configuredTreeUriOrNull(): Uri? {
        settingsDataStore.syncedTreeUri.first()?.let { return Uri.parse(it) }
        val legacy = settingsDataStore.legacySyncedFileUri.first()?.let(Uri::parse) ?: return null
        if (!DocumentsContract.isTreeUri(legacy)) return null
        settingsDataStore.setSyncedTreeUri(legacy.toString())
        return legacy
    }

    private suspend fun requireConfiguredTreeUri(): Uri = configuredTreeUriOrNull()
        ?: error("Connect a synced finance data directory in Settings first.")

    private fun displayName(uri: Uri): String = uri.lastPathSegment?.substringAfterLast(':') ?: "Finance data directory"

    private fun nowText(): String =
        LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))

    private companion object {
        val sharedMutex = Mutex()
    }
}
