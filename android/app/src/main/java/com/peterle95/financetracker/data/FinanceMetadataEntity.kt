package com.peterle95.financetracker.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "finance_metadata")
data class FinanceMetadataEntity(
    @PrimaryKey val id: Int = SINGLETON_ID,
    val budgetSettingsJson: String = "{}",
    val topLevelExtraJson: String = "{}",
) {
    companion object {
        const val SINGLETON_ID = 1
    }
}
