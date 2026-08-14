package com.peterle95.financetracker.data

import android.content.Context
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.PutDataRequest
import com.google.android.gms.wearable.Wearable
import com.peterle95.financetracker.domain.CategoryState
import com.peterle95.financetracker.protocol.CATEGORIES_PATH
import com.peterle95.financetracker.protocol.CategorySnapshot
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

class CategorySnapshotPublisher(context: Context) {
    private val appContext = context.applicationContext
    private val preferences = appContext.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    suspend fun publish(categories: CategoryState, requestSequence: Long) = publicationMutex.withLock {
        newestRequestSequence = newestCategoryPublicationRequest(newestRequestSequence, requestSequence)
            ?: return@withLock
        val next = nextCategorySnapshot(
            lastRevision = preferences.getLong(REVISION, 0),
            lastContent = preferences.getString(CONTENT, null),
            expense = categories.expenses,
            income = categories.incomes,
        ) ?: return@withLock
        withContext(Dispatchers.IO) {
            Tasks.await(
                Wearable.getDataClient(appContext).putDataItem(
                    PutDataRequest.create(CATEGORIES_PATH)
                        .setData(TransactionProtocolCodec.encodeCategories(next.snapshot))
                        .setUrgent(),
                ),
                PUBLISH_TIMEOUT_SECONDS,
                TimeUnit.SECONDS,
            )
        }
        check(
            preferences.edit()
                .putLong(REVISION, next.snapshot.revision)
                .putString(CONTENT, next.content)
                .commit(),
        )
    }

    private companion object {
        const val PREFERENCES = "watch_category_publication"
        const val REVISION = "revision"
        const val CONTENT = "content"
        const val PUBLISH_TIMEOUT_SECONDS = 20L
        val publicationMutex = Mutex()
        var newestRequestSequence = 0L
    }
}

internal data class PendingCategorySnapshot(val snapshot: CategorySnapshot, val content: String)

internal fun newestCategoryPublicationRequest(newestSeen: Long, requestSequence: Long): Long? =
    requestSequence.takeIf { it >= newestSeen }

internal fun nextCategorySnapshot(
    lastRevision: Long,
    lastContent: String?,
    expense: List<String>,
    income: List<String>,
): PendingCategorySnapshot? {
    val content = TransactionProtocolCodec.encodeCategories(
        CategorySnapshot(revision = 0, expenseCategories = expense, incomeCategories = income),
    ).decodeToString()
    if (content == lastContent) return null
    require(lastRevision < Long.MAX_VALUE) { "Category revision exhausted." }
    return PendingCategorySnapshot(
        CategorySnapshot(
            revision = lastRevision.coerceAtLeast(0) + 1,
            expenseCategories = expense,
            incomeCategories = income,
        ),
        content,
    )
}
