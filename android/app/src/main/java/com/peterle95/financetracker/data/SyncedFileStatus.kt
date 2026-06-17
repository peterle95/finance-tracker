package com.peterle95.financetracker.data

data class SyncedFileStatus(
    val uri: String? = null,
    val fileName: String? = null,
    val lastLoadedAt: String? = null,
    val lastWrittenAt: String? = null,
    val lastError: String? = null,
) {
    val isConnected: Boolean = uri != null
}
