package com.peterle95.financetracker.ui

import android.app.Application
import android.net.Uri
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.peterle95.financetracker.data.FinanceRepository
import com.peterle95.financetracker.data.SyncedFileStatus
import com.peterle95.financetracker.domain.BudgetSettings
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.DashboardSummary
import com.peterle95.financetracker.domain.FinanceAggregator
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.FixedCost
import com.peterle95.financetracker.domain.IncomeSource
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

    val budgetSettingsModel: StateFlow<BudgetSettings> = repository.budgetSettingsModel.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = BudgetSettings(),
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
            runCatching {
                repository.setCategories(type, categories)
            }.onSuccess {
                messages.emit("Categories updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update categories.")
            }
        }
    }

    fun updateBalances(
        bank: String,
        wallet: String,
        savings: String,
        investments: String,
        moneyLent: String,
    ) {
        viewModelScope.launch {
            runCatching {
                repository.updateBalances(
                    bank = parseAmount(bank, "Bank account balance"),
                    wallet = parseAmount(wallet, "Wallet balance"),
                    savings = parseAmount(savings, "Savings balance"),
                    investments = parseAmount(investments, "Investment balance"),
                    moneyLent = parseAmount(moneyLent, "Money lent balance"),
                )
            }.onSuccess {
                messages.emit("Balances updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update balances.")
            }
        }
    }

    fun setDailySavingsGoal(amount: String) {
        viewModelScope.launch {
            runCatching {
                repository.setDailySavingsGoal(parseAmount(amount, "Daily savings goal"))
            }.onSuccess {
                messages.emit("Daily savings goal updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update daily savings goal.")
            }
        }
    }

    fun addIncomeSource(amount: String, description: String, startDate: String, endDate: String) {
        viewModelScope.launch {
            runCatching {
                repository.addIncomeSource(incomeSourceFromInput(amount, description, startDate, endDate))
            }.onSuccess {
                messages.emit("Income source added.")
            }.onFailure {
                messages.emit(it.message ?: "Could not add income source.")
            }
        }
    }

    fun updateIncomeSource(key: String, amount: String, description: String, startDate: String, endDate: String) {
        viewModelScope.launch {
            runCatching {
                repository.updateIncomeSource(key, incomeSourceFromInput(amount, description, startDate, endDate))
            }.onSuccess {
                messages.emit("Income source updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update income source.")
            }
        }
    }

    fun archiveIncomeSource(key: String, endDate: String = LocalDate.now().toString()) {
        viewModelScope.launch {
            runCatching {
                requireIsoDate(endDate, "Archive date")
                repository.archiveIncomeSource(key, endDate)
            }.onSuccess {
                messages.emit("Income source archived.")
            }.onFailure {
                messages.emit(it.message ?: "Could not archive income source.")
            }
        }
    }

    fun deleteIncomeSource(key: String) {
        viewModelScope.launch {
            runCatching {
                repository.deleteIncomeSource(key)
            }.onSuccess {
                messages.emit("Income source deleted.")
            }.onFailure {
                messages.emit(it.message ?: "Could not delete income source.")
            }
        }
    }

    fun addFixedCost(amount: String, description: String, startDate: String, endDate: String) {
        viewModelScope.launch {
            runCatching {
                repository.addFixedCost(fixedCostFromInput(amount, description, startDate, endDate))
            }.onSuccess {
                messages.emit("Fixed cost added.")
            }.onFailure {
                messages.emit(it.message ?: "Could not add fixed cost.")
            }
        }
    }

    fun updateFixedCost(key: String, amount: String, description: String, startDate: String, endDate: String) {
        viewModelScope.launch {
            runCatching {
                repository.updateFixedCost(key, fixedCostFromInput(amount, description, startDate, endDate))
            }.onSuccess {
                messages.emit("Fixed cost updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update fixed cost.")
            }
        }
    }

    fun archiveFixedCost(key: String, endDate: String = LocalDate.now().toString()) {
        viewModelScope.launch {
            runCatching {
                requireIsoDate(endDate, "Archive date")
                repository.archiveFixedCost(key, endDate)
            }.onSuccess {
                messages.emit("Fixed cost archived.")
            }.onFailure {
                messages.emit(it.message ?: "Could not archive fixed cost.")
            }
        }
    }

    fun deleteFixedCost(key: String) {
        viewModelScope.launch {
            runCatching {
                repository.deleteFixedCost(key)
            }.onSuccess {
                messages.emit("Fixed cost deleted.")
            }.onFailure {
                messages.emit(it.message ?: "Could not delete fixed cost.")
            }
        }
    }

    fun setCategoryBudget(category: String, percent: String) {
        viewModelScope.launch {
            runCatching {
                require(category.isNotBlank()) { "Choose a category." }
                repository.setCategoryBudget(TransactionType.Expense, category, parseAmount(percent, "Budget percentage"))
            }.onSuccess {
                messages.emit("Category budget updated.")
            }.onFailure {
                messages.emit(it.message ?: "Could not update category budget.")
            }
        }
    }

    fun recordAssetSnapshot(date: String, note: String) {
        viewModelScope.launch {
            runCatching {
                requireIsoDate(date, "Snapshot date")
                repository.recordAssetSnapshot(date, note.trim())
            }.onSuccess {
                messages.emit("Asset snapshot recorded.")
            }.onFailure {
                messages.emit(it.message ?: "Could not record asset snapshot.")
            }
        }
    }

    fun deleteAssetSnapshot(date: String) {
        viewModelScope.launch {
            runCatching {
                requireIsoDate(date, "Snapshot date")
                repository.deleteAssetSnapshot(date)
            }.onSuccess {
                messages.emit("Asset snapshot deleted.")
            }.onFailure {
                messages.emit(it.message ?: "Could not delete asset snapshot.")
            }
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

    private fun incomeSourceFromInput(
        amount: String,
        description: String,
        startDate: String,
        endDate: String,
    ): IncomeSource {
        val trimmedDescription = description.trim()
        require(trimmedDescription.isNotBlank()) { "Income description cannot be empty." }
        return IncomeSource(
            amount = parseAmount(amount, "Income amount"),
            description = trimmedDescription,
            startDate = requireIsoDate(startDate, "Income start date"),
            endDate = optionalIsoDate(endDate, "Income end date"),
        )
    }

    private fun fixedCostFromInput(
        amount: String,
        description: String,
        startDate: String,
        endDate: String,
    ): FixedCost {
        val trimmedDescription = description.trim()
        require(trimmedDescription.isNotBlank()) { "Fixed cost description cannot be empty." }
        return FixedCost(
            amount = parseAmount(amount, "Fixed cost amount"),
            description = trimmedDescription,
            startDate = requireIsoDate(startDate, "Fixed cost start date"),
            endDate = optionalIsoDate(endDate, "Fixed cost end date"),
        )
    }

    private fun parseAmount(value: String, label: String): Double {
        val normalized = value.trim().replace(",", "")
        if (normalized.isBlank()) return 0.0
        return normalized.toDoubleOrNull() ?: error("$label must be a number.")
    }

    private fun requireIsoDate(value: String, label: String): String {
        val trimmed = value.trim()
        require(trimmed.matches(Regex("\\d{4}-\\d{2}-\\d{2}"))) { "$label must use YYYY-MM-DD." }
        LocalDate.parse(trimmed)
        return trimmed
    }

    private fun optionalIsoDate(value: String, label: String): String? {
        val trimmed = value.trim()
        if (trimmed.isBlank()) return null
        return requireIsoDate(trimmed, label)
    }
}
