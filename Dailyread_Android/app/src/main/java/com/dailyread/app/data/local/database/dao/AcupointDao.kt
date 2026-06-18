package com.dailyread.app.data.local.database.dao

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Update
import com.dailyread.app.data.local.database.entities.Acupoint
import kotlinx.coroutines.flow.Flow

@Dao
interface AcupointDao {
    @Insert
    suspend fun insert(acupoint: Acupoint): Long

    @Update
    suspend fun update(acupoint: Acupoint)

    @Delete
    suspend fun delete(acupoint: Acupoint)

    @Query("SELECT * FROM acupoints ORDER BY createTime DESC")
    fun getAllAcupoints(): Flow<List<Acupoint>>

    @Query("SELECT * FROM acupoints WHERE id = :id")
    suspend fun getAcupointById(id: Long): Acupoint?

    @Query("SELECT * FROM acupoints WHERE acupoint LIKE '%' || :query || '%' ORDER BY createTime DESC")
    suspend fun searchByAcupoint(query: String): List<Acupoint>

    @Query("SELECT * FROM acupoints WHERE meridian LIKE '%' || :meridian || '%' ORDER BY createTime DESC")
    suspend fun filterByMeridian(meridian: String): List<Acupoint>

    @Query("SELECT DISTINCT meridian FROM acupoints ORDER BY meridian")
    suspend fun getDistinctMeridians(): List<String>

    @Query("SELECT * FROM acupoints ORDER BY RANDOM() LIMIT 1")
    suspend fun getRandomAcupoint(): Acupoint?
    
    @Delete
    suspend fun deleteAcupoints(acupoints: List<Acupoint>)
}
