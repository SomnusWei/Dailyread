package com.dailyread.app.data.repository

import com.dailyread.app.data.local.database.dao.ContentCheckInDao
import com.dailyread.app.data.local.database.entities.ContentCheckIn
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CheckInRepository @Inject constructor(
    private val contentCheckInDao: ContentCheckInDao
) {
    fun getCheckInsByContent(contentId: Long): Flow<List<String>> =
        contentCheckInDao.getCheckInsByContent(contentId)

    suspend fun getCheckInDataByYear(yearPrefix: String): List<ContentCheckIn> =
        contentCheckInDao.getCheckInDataByYear(yearPrefix)

    suspend fun getAllCheckInRecords(): List<ContentCheckIn> =
        contentCheckInDao.getAllCheckInRecords()

    suspend fun getCheckInsByContentId(contentId: Long): List<ContentCheckIn> =
        contentCheckInDao.getCheckInsByContentId(contentId)

    suspend fun insertCheckIn(checkIn: ContentCheckIn): Long =
        contentCheckInDao.insertCheckIn(checkIn)

    suspend fun insertAllCheckIns(checkIns: List<ContentCheckIn>) =
        contentCheckInDao.insertAllCheckIns(checkIns)

    suspend fun deleteCheckIn(checkIn: ContentCheckIn) =
        contentCheckInDao.deleteCheckIn(checkIn)

    suspend fun deleteCheckInByDate(contentId: Long, date: String) =
        contentCheckInDao.deleteCheckInByDate(contentId, date)

    suspend fun deleteCheckInsByContent(contentId: Long) =
        contentCheckInDao.deleteCheckInsByContent(contentId)

    suspend fun deleteAllCheckIns() =
        contentCheckInDao.deleteAllCheckIns()
}
