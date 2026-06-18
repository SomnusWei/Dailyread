package com.dailyread.app.data.local.database.dao
import androidx.room.*
import com.dailyread.app.data.local.database.entities.Content
import kotlinx.coroutines.flow.Flow

@Dao
interface ContentDao {
    @Query("SELECT * FROM contents ORDER BY createTime DESC")
    fun getAllContents(): Flow<List<Content>>

    @Query("SELECT * FROM contents WHERE isReading = 1 ORDER BY createTime DESC")
    fun getReadingContents(): Flow<List<Content>>

    @Query("SELECT * FROM contents WHERE isReading = 1 AND isRequired = 0 ORDER BY createTime DESC")
    fun getPoolContents(): Flow<List<Content>>

    @Query("SELECT * FROM contents WHERE isReading = 1 AND isRequired = 1 ORDER BY createTime DESC")
    fun getRequiredContents(): Flow<List<Content>>

    @Query("SELECT * FROM contents WHERE id = :id")
    suspend fun getContentById(id: Long): Content?

    @Query("SELECT * FROM contents")
    suspend fun getAllContentsOnce(): List<Content>

    @Insert
    suspend fun insertContent(content: Content): Long

    @Update
    suspend fun updateContent(content: Content)

    @Delete
    suspend fun deleteContent(content: Content)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(contents: List<Content>)
}