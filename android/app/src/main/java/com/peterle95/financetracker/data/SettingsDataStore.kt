package com.peterle95.financetracker.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.financeDataStore by preferencesDataStore(name = "finance_settings")

class SettingsDataStore(private val context: Context) {
    val syncedFileUri: Flow<String?> = context.financeDataStore.data.map { prefs ->
        prefs[syncedFileUriKey]
    }

    suspend fun setSyncedFileUri(uri: String) {
        context.financeDataStore.edit { prefs ->
            prefs[syncedFileUriKey] = uri
        }
    }

    companion object {
        private val syncedFileUriKey = stringPreferencesKey("synced_file_uri")
    }
}
