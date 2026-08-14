package com.peterle95.financetracker.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.financeDataStore by preferencesDataStore(name = "finance_settings")

class SettingsDataStore(private val context: Context) {
    val syncedTreeUri: Flow<String?> = context.financeDataStore.data.map { prefs ->
        prefs[syncedTreeUriKey]
    }

    val legacySyncedFileUri: Flow<String?> = context.financeDataStore.data.map { prefs ->
        prefs[legacySyncedFileUriKey]
    }

    suspend fun setSyncedTreeUri(uri: String) {
        context.financeDataStore.edit { prefs ->
            prefs[syncedTreeUriKey] = uri
        }
    }

    companion object {
        private val syncedTreeUriKey = stringPreferencesKey("synced_tree_uri")
        private val legacySyncedFileUriKey = stringPreferencesKey("synced_file_uri")
    }
}
