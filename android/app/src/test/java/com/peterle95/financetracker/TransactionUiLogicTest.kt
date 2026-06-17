package com.peterle95.financetracker

import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionUiLogic
import com.peterle95.financetracker.domain.TransactionType
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertThrows
import org.junit.Test
import java.time.YearMonth

class TransactionUiLogicTest {
    @Test
    fun normalExpenseKeepsSelectedDate() {
        val dates = TransactionUiLogic.bookingDatesFor(
            type = TransactionType.Expense,
            selectedDate = "2026-06-16",
            isBnpl = false,
        )

        assertEquals("2026-06-16", dates.date)
        assertNull(dates.behaviorDate)
    }

    @Test
    fun bnplExpenseBooksFirstDayOfNextMonth() {
        val dates = TransactionUiLogic.bookingDatesFor(
            type = TransactionType.Expense,
            selectedDate = "2026-06-16",
            isBnpl = true,
        )

        assertEquals("2026-07-01", dates.date)
        assertEquals("2026-06-16", dates.behaviorDate)
    }

    @Test
    fun bnplExpenseHandlesYearBoundary() {
        val dates = TransactionUiLogic.bookingDatesFor(
            type = TransactionType.Expense,
            selectedDate = "2026-12-15",
            isBnpl = true,
        )

        assertEquals("2027-01-01", dates.date)
        assertEquals("2026-12-15", dates.behaviorDate)
    }

    @Test
    fun bnplIsRejectedForIncome() {
        assertThrows(IllegalArgumentException::class.java) {
            TransactionUiLogic.bookingDatesFor(
                type = TransactionType.Income,
                selectedDate = "2026-06-16",
                isBnpl = true,
            )
        }
    }

    @Test
    fun monthOptionsIncludeCurrentMonthAndTransactionMonthsNewestFirst() {
        val months = TransactionUiLogic.availableMonthKeys(
            transactions = rows,
            currentMonth = YearMonth.of(2026, 8),
        )

        assertEquals(listOf("2026-08", "2026-07", "2026-06"), months)
    }

    @Test
    fun monthFilterUsesBookingDateNotBehaviorDate() {
        val july = TransactionUiLogic.filterTransactions(
            transactions = rows,
            selectedMonthKey = "2026-07",
            categoryFilter = "All",
            typeFilter = null,
            searchText = "",
        )
        val june = TransactionUiLogic.filterTransactions(
            transactions = rows,
            selectedMonthKey = "2026-06",
            categoryFilter = "All",
            typeFilter = null,
            searchText = "",
        )

        assertEquals(listOf("bnpl", "july-income"), july.map { it.uiKey })
        assertEquals(listOf("june-food"), june.map { it.uiKey })
    }

    @Test
    fun allMonthsShowsAllTransactions() {
        val filtered = TransactionUiLogic.filterTransactions(
            transactions = rows,
            selectedMonthKey = TransactionUiLogic.ALL_MONTHS_KEY,
            categoryFilter = "All",
            typeFilter = null,
            searchText = "",
        )

        assertEquals(rows.map { it.uiKey }, filtered.map { it.uiKey })
    }

    @Test
    fun monthAndCategoryFiltersCombine() {
        val filtered = TransactionUiLogic.filterTransactions(
            transactions = rows,
            selectedMonthKey = "2026-07",
            categoryFilter = "Food",
            typeFilter = TransactionType.Expense,
            searchText = "klarna",
        )

        assertEquals(listOf("bnpl"), filtered.map { it.uiKey })
    }

    private val rows = listOf(
        FinanceTransaction("bnpl", "bnpl", TransactionType.Expense, "2026-07-01", 45.0, "Food", "Klarna", "2026-06-16"),
        FinanceTransaction("july-income", "july-income", TransactionType.Income, "2026-07-15", 100.0, "Gift", "Gift", null),
        FinanceTransaction("june-food", "june-food", TransactionType.Expense, "2026-06-20", 12.0, "Food", "Lunch", null),
    )
}
