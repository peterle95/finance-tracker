package com.peterle95.financetracker.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.peterle95.financetracker.data.FinanceRepository
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.DashboardSummary
import com.peterle95.financetracker.domain.FinanceAggregator
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.InsightsJson
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.buildJsonObject
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

    val dashboard: StateFlow<DashboardSummary> = combine(transactions, budgetSettings) { rows, budget ->
        FinanceAggregator.buildDashboardSummary(rows, budget, YearMonth.now())
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = FinanceAggregator.buildDashboardSummary(emptyList(), buildJsonObject {}, YearMonth.now()),
    )

    val insightsJson: StateFlow<String> = combine(transactions, budgetSettings) { rows, budget ->
        InsightsJson.encode(FinanceAggregator.buildInsightsSummary(rows, budget, YearMonth.now(), monthsBack = 3))
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = "{}",
    )

    val messages = MutableSharedFlow<String>()

    fun addTransaction(
        type: TransactionType,
        amountText: String,
        category: String,
        description: String,
        date: String,
    ) {
        viewModelScope.launch {
            runCatching {
                val amount = amountText.trim().toDouble()
                require(amount > 0.0) { "Amount must be greater than zero." }
                require(date.matches(Regex("\\d{4}-\\d{2}-\\d{2}"))) { "Date must use YYYY-MM-DD." }
                require(category.isNotBlank()) { "Choose a category." }
                repository.addTransaction(
                    type = type,
                    date = date,
                    amount = amount,
                    category = category,
                    description = description.trim(),
                )
            }.onSuccess {
                messages.emit("Transaction saved.")
            }.onFailure {
                messages.emit(it.message ?: "Could not save transaction.")
            }
        }
    }

    fun deleteTransaction(localId: Long) {
        viewModelScope.launch {
            repository.deleteTransaction(localId)
            messages.emit("Transaction deleted.")
        }
    }

    fun setCategories(type: TransactionType, categories: List<String>) {
        viewModelScope.launch {
            repository.setCategories(type, categories)
            messages.emit("Categories updated.")
        }
    }

    fun importJson(uri: Uri) {
        viewModelScope.launch {
            runCatching {
                repository.importFromUri(getApplication<Application>().contentResolver, uri)
            }.onSuccess {
                messages.emit("Imported finance_data.json.")
            }.onFailure {
                messages.emit(it.message ?: "Import failed.")
            }
        }
    }

    fun exportJson(uri: Uri) {
        viewModelScope.launch {
            runCatching {
                repository.exportToUri(getApplication<Application>().contentResolver, uri)
            }.onSuccess {
                messages.emit("Exported finance_data.json.")
            }.onFailure {
                messages.emit(it.message ?: "Export failed.")
            }
        }
    }
}
