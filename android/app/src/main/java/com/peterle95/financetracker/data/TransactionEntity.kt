package com.peterle95.financetracker.data

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.peterle95.financetracker.domain.FinanceTransaction
import com.peterle95.financetracker.domain.TransactionType

@Entity(tableName = "transactions")
data class TransactionEntity(
    @PrimaryKey(autoGenerate = true) val localId: Long = 0,
    val exportId: String?,
    val type: String,
    val date: String,
    val amount: Double,
    val category: String,
    val description: String,
    val behaviorDate: String?,
    val extraJson: String,
    val createdAt: Long,
    val updatedAt: Long,
) {
    fun toDomain(): FinanceTransaction =
        FinanceTransaction(
            localId = localId,
            exportId = exportId,
            type = TransactionType.fromLabel(type),
            date = date,
            amount = amount,
            category = category,
            description = description,
            behaviorDate = behaviorDate,
        )
}

fun FinanceTransaction.toEntity(extraJson: String = "{}"): TransactionEntity {
    val now = System.currentTimeMillis()
    return TransactionEntity(
        localId = localId,
        exportId = exportId,
        type = type.label,
        date = date,
        amount = amount,
        category = category,
        description = description,
        behaviorDate = behaviorDate,
        extraJson = extraJson,
        createdAt = now,
        updatedAt = now,
    )
}
