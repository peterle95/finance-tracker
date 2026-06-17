package com.peterle95.financetracker.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.peterle95.financetracker.data.FinanceRepository
import com.peterle95.financetracker.data.SyncedFileStatus
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.DashboardSummary
import com.peterle95.financetracker.domain.FinanceAggregator
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionUiLogic
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
import java.time.LocalDate
import java.time.YearMonth

class FinanceViewModel(application: Application) : AndroidViewModel(application) {
    private val repository = FinanceRepository(application)

    val transactions: StateFlow<List<FinanceTransaction>> = repository.transactions.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = emptyList(),
    )

    val categories: StateFlow<CategoryState> = repository.categories.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = CategoryState(),
    )

    val budgetSettings: StateFlow<JsonObject> = repository.budgetSettings.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = buildJsonObject {},
    )

    val syncStatus: StateFlow<SyncedFileStatus> = repository.syncStatus.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = SyncedFileStatus(),
    )

    val dashboard: StateFlow<DashboardSummary> = combine(transactions, budgetSettings) { rows, budget ->
        FinanceAggregator.buildDashboardSummary(rows, budget, YearMonth.now())
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = FinanceAggregator.buildDashboardSummary(emptyList(), buildJsonObject {}, YearMonth.now()),
    )

    val messages = MutableSharedFlow<String>()

    init {
        viewModelScope.launch {
            runCatching { repository.loadConfiguredFileIfAny() }
        }
    }

    fun addTransaction(
        type: TransactionType,
        amountText: String,
        category: String,
        description: String,
        date: String,
        isBnpl: Boolean = false,
    ) {
        viewModelScope.launch {
            runCatching {
                val amount = amountText.trim().toDouble()
                require(amount > 0.0) { "Amount must be greater than zero." }
                require(date.matches(Regex("\\d{4}-\\d{2}-\\d{2}"))) { "Date must use YYYY-MM-DD." }
                LocalDate.parse(date)
                require(category.isNotBlank()) { "Choose a category." }
                val bookingDates = TransactionUiLogic.bookingDatesFor(type, date, isBnpl)
                repository.addTransaction(
                    type = type,
                    date = bookingDates.date,
                    amount = amount,
                    category = category,
                    description = description.trim(),
                    behaviorDate = bookingDates.behaviorDate,
                )
            }.onSuccess {
                messages.emit("Transaction saved.")
            }.onFailure {
                messages.emit(it.message ?: "Could not save transaction.")
            }
        }
    }

    fun deleteTransaction(exportId: String?) {
        viewModelScope.launch {
            runCatching {
                require(!exportId.isNullOrBlank()) { "This transaction has no JSON id and cannot be deleted from Android." }
                repository.deleteTransaction(exportId)
            }.onSuccess {
                messages.emit("Transaction deleted.")
            }.onFailure {
                messages.emit(it.message ?: "Could not delete transaction.")
            }
        }
    }

    fun setCategories(type: TransactionType, categories: List<String>) {
        viewModelScope.launch {
            repository.setCategories(type, categories)
            messages.emit("Categories updated.")
        }
    }

    fun connectSyncedFile(uri: Uri) {
        viewModelScope.launch {
            runCatching {
                repository.connectSyncedFile(uri)
            }.onSuccess {
                messages.emit("Connected finance_data.json.")
            }.onFailure {
                messages.emit(it.message ?: "Could not connect file.")
            }
        }
    }

    fun reloadFromSyncedFile(showMessage: Boolean = true) {
        viewModelScope.launch {
            runCatching {
                repository.loadConfiguredFileIfAny()
            }.onSuccess {
                if (showMessage) messages.emit("Reloaded synced file.")
            }.onFailure {
                if (showMessage) messages.emit(it.message ?: "Reload failed.")
            }
        }
    }
}
