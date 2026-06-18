package com.dailyread.app.data.local.database.dao

import androidx.room.*
import com.dailyread.app.data.local.database.entities.Concept
import kotlinx.coroutines.flow.Flow

@Dao
interface ConceptDao {
    @Query("SELECT * FROM concepts ORDER BY createTime DESC")
    fun getAllConcepts(): Flow<List<Concept>>

    @Query("SELECT * FROM concepts ORDER BY createTime DESC")
    suspend fun getAllConceptsOnce(): List<Concept>

    @Query("SELECT * FROM concepts WHERE isEnabled = 1 ORDER BY createTime DESC")
    fun getEnabledConcepts(): Flow<List<Concept>>

    @Query("SELECT * FROM concepts WHERE id = :id")
    suspend fun getConceptById(id: Long): Concept?

    @Query("SELECT DISTINCT subject FROM concepts ORDER BY subject")
    fun getAllSubjects(): Flow<List<String>>

    @Query("SELECT DISTINCT category FROM concepts ORDER BY category")
    fun getAllCategories(): Flow<List<String>>

    @Query("SELECT DISTINCT subChapter FROM concepts WHERE category = :category ORDER BY subChapter")
    fun getSubChaptersByCategory(category: String): Flow<List<String>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConcept(concept: Concept): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConcepts(concepts: List<Concept>)

    @Update
    suspend fun updateConcept(concept: Concept)

    @Delete
    suspend fun deleteConcept(concept: Concept)

    @Query("DELETE FROM concepts WHERE id IN (:ids)")
    suspend fun deleteConcepts(ids: List<Long>)

    @Delete
    suspend fun deleteConceptsList(concepts: List<Concept>)

    @Query("DELETE FROM concepts")
    suspend fun deleteAllConcepts()

    @Query("SELECT * FROM concepts ORDER BY RANDOM() LIMIT 1")
    suspend fun getRandomConcept(): Concept?

    @Query("SELECT * FROM concepts WHERE title LIKE '%' || :query || '%' ORDER BY createTime DESC")
    suspend fun searchByTitle(query: String): List<Concept>

    @Query("SELECT * FROM concepts WHERE subject LIKE '%' || :subject || '%' ORDER BY createTime DESC")
    suspend fun filterBySubject(subject: String): List<Concept>

    @Query("SELECT * FROM concepts WHERE category LIKE '%' || :category || '%' ORDER BY createTime DESC")
    suspend fun filterByCategory(category: String): List<Concept>

    @Query("SELECT * FROM concepts WHERE category = :category AND subject = :subject AND subChapter = :subChapter ORDER BY createTime DESC")
    suspend fun filterByAll(category: String, subject: String, subChapter: String): List<Concept>

    @Query("SELECT * FROM concepts WHERE category = :category AND subject = :subject ORDER BY createTime DESC")
    suspend fun filterByCategoryAndSubject(category: String, subject: String): List<Concept>

    @Query("SELECT * FROM concepts WHERE category = :category ORDER BY createTime DESC")
    suspend fun filterByExactCategory(category: String): List<Concept>

    @Query("SELECT DISTINCT subject FROM concepts WHERE category = :category ORDER BY subject")
    suspend fun getSubjectsByCategory(category: String): List<String>

    @Query("SELECT DISTINCT subChapter FROM concepts WHERE category = :category AND subject = :subject ORDER BY subChapter")
    suspend fun getSubChaptersByCategoryAndSubject(category: String, subject: String): List<String>
}
