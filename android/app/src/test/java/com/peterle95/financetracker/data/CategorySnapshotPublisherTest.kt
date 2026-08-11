package com.peterle95.financetracker.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class CategorySnapshotPublisherTest {
    @Test
    fun contentChangesAdvanceDurableRevisionOnlyOnce() {
        val first = requireNotNull(nextCategorySnapshot(0, null, listOf("Food"), listOf("Salary")))

        assertEquals(1, first.snapshot.revision)
        assertNull(nextCategorySnapshot(first.snapshot.revision, first.content, listOf("Food"), listOf("Salary")))
        assertEquals(2L, nextCategorySnapshot(first.snapshot.revision, first.content, listOf("Travel"), listOf("Salary"))?.snapshot?.revision)
    }

    @Test
    fun unpublishedContentRetriesWithSameNextRevision() {
        val firstAttempt = requireNotNull(nextCategorySnapshot(4, "old", listOf("Travel"), listOf("Salary")))
        val retry = requireNotNull(nextCategorySnapshot(4, "old", listOf("Travel"), listOf("Salary")))

        assertEquals(5, firstAttempt.snapshot.revision)
        assertEquals(firstAttempt, retry)
    }

    @Test
    fun stalePublicationRequestIsDroppedAfterNewerRequestArrives() {
        val newest = requireNotNull(newestCategoryPublicationRequest(0, 2))

        assertNull(newestCategoryPublicationRequest(newest, 1))
    }
}
