package com.dailyread.app.data.local.database.dao

import androidx.room.*
import com.dailyread.app.data.local.database.entities.ContentCheckIn
import kotlinx.coroutines.flow.Flow

@Dao
interface ContentCheckInDao {
    @Query("SELECT date FROM content_checkin WHERE contentId = :contentId ORDER BY date")
    fun getCheckInsByContent(contentId: Long): Flow<List<String>>

    @Query("SELECT * FROM content_checkin WHERE date LIKE :yearPrefix || '%' ORDER BY date")
    suspend fun getCheckInDataByYear(yearPrefix: String): List<ContentCheckIn>

    @Query("SELECT * FROM content_checkin")
    suspend fun getAllCheckInRecords(): List<ContentCheckIn>

    @Query("SELECT * FROM content_checkin WHERE contentId = :contentId")
    suspend fun getCheckInsByContentId(contentId: Long): List<ContentCheckIn>

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertCheckIn(checkIn: ContentCheckIn): Long

    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertAllCheckIns(checkIns: List<ContentCheckIn>)

    @Delete
    suspend fun deleteCheckIn(checkIn: ContentCheckIn)

    @Query("DELETE FROM content_checkin WHERE contentId = :contentId AND date = :date")
    suspend fun deleteCheckInByDate(contentId: Long, date: String)

    @Query("DELETE FROM content_checkin WHERE contentId = :contentId")
    suspend fun deleteCheckInsByContent(contentId: Long)

    @Query("DELETE FROM content_checkin")
    suspend fun deleteAllCheckIns()
}
