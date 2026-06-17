package com.peterle95.financetracker.domain

import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.util.Locale

data class TransactionBookingDates(
    val date: String,
    val behaviorDate: String?,
)

object TransactionUiLogic {
    const val ALL_MONTHS_KEY = "ALL"

    private val monthFormatter = DateTimeFormatter.ofPattern("MMMM yyyy", Locale.ENGLISH)

    fun bookingDatesFor(type: TransactionType, selectedDate: String, isBnpl: Boolean): TransactionBookingDates {
        require(!(isBnpl && type != TransactionType.Expense)) { "BNPL is only available for expenses." }
        return if (isBnpl) {
            TransactionBookingDates(
                date = bookedDateForBnpl(selectedDate),
                behaviorDate = selectedDate,
            )
        } else {
            TransactionBookingDates(date = selectedDate, behaviorDate = null)
        }
    }

    fun bookedDateForBnpl(selectedDate: String): String =
        LocalDate.parse(selectedDate)
            .plusMonths(1)
            .withDayOfMonth(1)
            .toString()

    fun availableMonthKeys(
        transactions: List<FinanceTransaction>,
        currentMonth: YearMonth = YearMonth.now(),
    ): List<String> =
        (transactions.mapNotNull { transaction ->
            runCatching { YearMonth.parse(transaction.date.take(7)) }.getOrNull()
        } + currentMonth)
            .distinct()
            .sortedDescending()
            .map { it.toString() }

    fun monthLabel(monthKey: String): String =
        if (monthKey == ALL_MONTHS_KEY) {
            "All months"
        } else {
            YearMonth.parse(monthKey).format(monthFormatter)
        }

    fun filterTransactions(
        transactions: List<FinanceTransaction>,
        selectedMonthKey: String,
        categoryFilter: String,
        typeFilter: TransactionType?,
        searchText: String,
    ): List<FinanceTransaction> {
        val normalizedSearch = searchText.trim()
        return transactions.filter { row ->
            val rowMonth = row.date.take(7)
            (selectedMonthKey == ALL_MONTHS_KEY || rowMonth == selectedMonthKey) &&
                (typeFilter == null || row.type == typeFilter) &&
                (categoryFilter.isBlank() || categoryFilter == "All" || row.category == categoryFilter) &&
                (
                    normalizedSearch.isBlank() ||
                        row.description.contains(normalizedSearch, ignoreCase = true)
                    )
        }
    }
}
