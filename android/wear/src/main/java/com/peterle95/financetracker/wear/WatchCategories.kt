package com.peterle95.financetracker.wear

import android.content.Context
import com.google.android.gms.tasks.Tasks
import com.google.android.gms.wearable.Wearable
import com.peterle95.financetracker.protocol.CATEGORIES_PATH
import com.peterle95.financetracker.protocol.CategorySnapshot
import com.peterle95.financetracker.protocol.CategorySnapshotDefaults
import com.peterle95.financetracker.protocol.TransactionProtocolCodec
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

object WatchCategoryCache {
    private val state = MutableStateFlow(CategorySnapshotDefaults.snapshot())
    private var initialized = false

    fun snapshots(context: Context): StateFlow<CategorySnapshot> = synchronized(this) {
        if (!initialized) {
            val payload = preferences(context).getString(PAYLOAD, null)?.encodeToByteArray()
            state.value = payload?.let(TransactionProtocolCodec::decodeCategories) ?: CategorySnapshotDefaults.snapshot()
            initialized = true
        }
        state
    }

    fun accept(context: Context, payload: ByteArray): Boolean =
        accept(context, payload, authoritative = false) == CategorySnapshotAcceptance.Accepted

    private fun accept(context: Context, payload: ByteArray, authoritative: Boolean): CategorySnapshotAcceptance = synchronized(this) {
        val candidate = TransactionProtocolCodec.decodeCategories(payload) ?: return CategorySnapshotAcceptance.Rejected
        val current = snapshots(context).value
        if (shouldRefreshCanonicalCategories(current, candidate, authoritative)) return CategorySnapshotAcceptance.Stale
        if (!shouldAcceptCategorySnapshot(current, candidate, authoritative)) return CategorySnapshotAcceptance.Rejected
        if (!preferences(context).edit().putString(PAYLOAD, payload.decodeToString()).commit()) {
            return CategorySnapshotAcceptance.Rejected
        }
        state.value = candidate
        CategorySnapshotAcceptance.Accepted
    }

    suspend fun refresh(context: Context) = withContext(Dispatchers.IO) {
        val items = Tasks.await(
            Wearable.getDataClient(context.applicationContext).dataItems,
            REFRESH_TIMEOUT_SECONDS,
            TimeUnit.SECONDS,
        )
        try {
            items.filter { it.uri.path == CATEGORIES_PATH }.forEach { item ->
                item.data?.let { accept(context, it, authoritative = true) }
            }
        } finally {
            items.release()
        }
    }

    fun accept(context: Context, payloads: Iterable<ByteArray>): Boolean {
        var refreshNeeded = false
        payloads.forEach {
            refreshNeeded = accept(context, it, authoritative = false) == CategorySnapshotAcceptance.Stale || refreshNeeded
        }
        return refreshNeeded
    }

    private fun preferences(context: Context) =
        context.applicationContext.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)

    private const val PREFERENCES = "watch_categories"
    private const val PAYLOAD = "payload"
    private const val REFRESH_TIMEOUT_SECONDS = 20L
}

private enum class CategorySnapshotAcceptance { Accepted, Stale, Rejected }

internal fun shouldAcceptCategorySnapshot(current: CategorySnapshot, candidate: CategorySnapshot, authoritative: Boolean) =
    authoritative || candidate.revision > current.revision

internal fun shouldRefreshCanonicalCategories(current: CategorySnapshot, candidate: CategorySnapshot, authoritative: Boolean) =
    !authoritative && candidate.revision <= current.revision
