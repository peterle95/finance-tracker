package com.peterle95.financetracker.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.peterle95.financetracker.domain.CategoryDefaults
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.domain.TransactionType
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.builtins.ListSerializer
import kotlinx.serialization.builtins.serializer
import kotlinx.serialization.json.Json

private val Context.financeDataStore by preferencesDataStore(name = "finance_settings")

class SettingsDataStore(private val context: Context) {
    private val json = Json

    val categories: Flow<CategoryState> = context.financeDataStore.data.map { prefs ->
        CategoryState(
            expenses = prefs[expenseCategoriesKey].decodeStringList(CategoryDefaults.expense),
            incomes = prefs[incomeCategoriesKey].decodeStringList(CategoryDefaults.income),
        )
    }

    suspend fun replaceCategories(expense: List<String>, income: List<String>) {
        context.financeDataStore.edit { prefs ->
            prefs[expenseCategoriesKey] = expense.normalized(CategoryDefaults.expense).encodeStringList()
            prefs[incomeCategoriesKey] = income.normalized(CategoryDefaults.income).encodeStringList()
        }
    }

    suspend fun setCategories(type: TransactionType, categories: List<String>) {
        context.financeDataStore.edit { prefs ->
            val defaults = if (type == TransactionType.Expense) CategoryDefaults.expense else CategoryDefaults.income
            prefs[if (type == TransactionType.Expense) expenseCategoriesKey else incomeCategoriesKey] =
                categories.normalized(defaults).encodeStringList()
        }
    }

    private fun String?.decodeStringList(defaults: List<String>): List<String> =
        runCatching {
            if (this == null) defaults else json.decodeFromString(ListSerializer(String.serializer()), this)
        }.getOrDefault(defaults).normalized(defaults)

    private fun List<String>.encodeStringList(): String =
        json.encodeToString(ListSerializer(String.serializer()), this)

    private fun List<String>.normalized(defaults: List<String>): List<String> =
        map { it.trim() }
            .filter { it.isNotEmpty() }
            .distinctBy { it.lowercase() }
            .ifEmpty { defaults }

    companion object {
        private val expenseCategoriesKey = stringPreferencesKey("expense_categories")
        private val incomeCategoriesKey = stringPreferencesKey("income_categories")
    }
}
