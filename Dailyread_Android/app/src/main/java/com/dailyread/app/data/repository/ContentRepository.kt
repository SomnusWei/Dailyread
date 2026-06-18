package com.dailyread.app.data.repository

import com.dailyread.app.data.local.database.dao.ContentDao
import com.dailyread.app.data.local.database.entities.Content
import kotlinx.coroutines.flow.Flow
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ContentRepository @Inject constructor(
    private val contentDao: ContentDao
) {
    fun getAllContents(): Flow<List<Content>> = contentDao.getAllContents()

    fun getReadingContents(): Flow<List<Content>> = contentDao.getReadingContents()

    fun getPoolContents(): Flow<List<Content>> = contentDao.getPoolContents()

    fun getRequiredContents(): Flow<List<Content>> = contentDao.getRequiredContents()

    suspend fun getContentById(id: Long): Content? = contentDao.getContentById(id)

    suspend fun getAllContentsOnce(): List<Content> = contentDao.getAllContentsOnce()

    suspend fun insertContent(content: Content): Long = contentDao.insertContent(content)

    suspend fun updateContent(content: Content) = contentDao.updateContent(content)

    suspend fun deleteContent(content: Content) = contentDao.deleteContent(content)

    suspend fun insertAll(contents: List<Content>) = contentDao.insertAll(contents)
}
