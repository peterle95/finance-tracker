package com.peterle95.financetracker.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface TransactionDao {
    @Query("SELECT * FROM transactions ORDER BY date DESC, localId DESC")
    fun observeAll(): Flow<List<TransactionEntity>>

    @Query("SELECT * FROM transactions ORDER BY date DESC, localId DESC")
    suspend fun getAll(): List<TransactionEntity>

    @Insert
    suspend fun insert(entity: TransactionEntity): Long

    @Insert
    suspend fun insertAll(entities: List<TransactionEntity>)

    @Query("DELETE FROM transactions WHERE localId = :localId")
    suspend fun deleteById(localId: Long)

    @Query("DELETE FROM transactions")
    suspend fun clear()
}

@Dao
interface MetadataDao {
    @Query("SELECT * FROM finance_metadata WHERE id = 1")
    fun observe(): Flow<FinanceMetadataEntity?>

    @Query("SELECT * FROM finance_metadata WHERE id = 1")
    suspend fun get(): FinanceMetadataEntity?

    @Upsert
    suspend fun upsert(entity: FinanceMetadataEntity)

    @Query("DELETE FROM finance_metadata")
    suspend fun clear()
}
