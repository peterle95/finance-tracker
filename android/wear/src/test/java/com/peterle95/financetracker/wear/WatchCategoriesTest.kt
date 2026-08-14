package com.peterle95.financetracker.wear

import com.peterle95.financetracker.protocol.CategorySnapshot
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class WatchCategoriesTest {
    @Test
    fun eventAcceptsOnlyHigherRevisions() {
        val current = CategorySnapshot(
            revision = 4,
            expenseCategories = listOf("Food"),
            incomeCategories = listOf("Salary"),
        )

        assertFalse(shouldAcceptCategorySnapshot(current, current.copy(revision = 3), authoritative = false))
        assertTrue(shouldRefreshCanonicalCategories(current, current.copy(revision = 3), authoritative = false))
        assertTrue(shouldRefreshCanonicalCategories(current, current.copy(revision = 4), authoritative = false))
        assertTrue(shouldAcceptCategorySnapshot(current, current.copy(revision = 5), authoritative = false))
        assertFalse(shouldRefreshCanonicalCategories(current, current.copy(revision = 5), authoritative = false))
    }

    @Test
    fun authoritativeRefreshAcceptsLowerRevision() {
        val current = CategorySnapshot(
            revision = 4,
            expenseCategories = listOf("Food"),
            incomeCategories = listOf("Salary"),
        )

        assertTrue(shouldAcceptCategorySnapshot(current, current.copy(revision = 1), authoritative = true))
        assertFalse(shouldRefreshCanonicalCategories(current, current.copy(revision = 1), authoritative = true))
    }
}
