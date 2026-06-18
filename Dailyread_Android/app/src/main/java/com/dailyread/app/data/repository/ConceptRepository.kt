package com.dailyread.app.data.repository

import android.content.Context
import com.dailyread.app.data.local.database.dao.ConceptDao
import com.dailyread.app.data.local.database.entities.Concept
import com.dailyread.app.domain.usecase.AutoSyncManager
import dagger.Lazy
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConceptRepository @Inject constructor(
    private val conceptDao: ConceptDao,
    private val autoSyncManagerLazy: Lazy<AutoSyncManager>,
    @ApplicationContext private val context: Context
) {

    fun getAllConcepts(): Flow<List<Concept>> = conceptDao.getAllConcepts()

    suspend fun getAllConceptsOnce(): List<Concept> = conceptDao.getAllConceptsOnce()

    fun getEnabledConcepts(): Flow<List<Concept>> = conceptDao.getEnabledConcepts()

    fun getAllSubjects(): Flow<List<String>> = conceptDao.getAllSubjects()

    fun getAllCategories(): Flow<List<String>> = conceptDao.getAllCategories()

    fun getSubChaptersByCategory(category: String): Flow<List<String>> = conceptDao.getSubChaptersByCategory(category)

    suspend fun getConceptById(id: Long): Concept? = conceptDao.getConceptById(id)

    suspend fun insertConcept(concept: Concept): Long {
        val id = conceptDao.insertConcept(concept)
        autoSyncManagerLazy.get().triggerAutoSync()
        return id
    }

    suspend fun insertConcepts(concepts: List<Concept>) {
        conceptDao.insertConcepts(concepts)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun updateConcept(concept: Concept) {
        conceptDao.updateConcept(concept)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun deleteConcept(concept: Concept) {
        conceptDao.deleteConcept(concept)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun deleteConcepts(ids: List<Long>) {
        conceptDao.deleteConcepts(ids)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun deleteConceptsList(concepts: List<Concept>) {
        conceptDao.deleteConceptsList(concepts)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun deleteAllConcepts() = conceptDao.deleteAllConcepts()

    suspend fun getRandomConcept(): Concept? = conceptDao.getRandomConcept()

    suspend fun searchByTitle(query: String): List<Concept> = conceptDao.searchByTitle(query)

    suspend fun filterBySubject(subject: String): List<Concept> = conceptDao.filterBySubject(subject)

    suspend fun filterByCategory(category: String): List<Concept> = conceptDao.filterByCategory(category)

    suspend fun filterByExactCategory(category: String): List<Concept> = conceptDao.filterByExactCategory(category)

    suspend fun filterByCategoryAndSubject(category: String, subject: String): List<Concept> = 
        conceptDao.filterByCategoryAndSubject(category, subject)

    suspend fun filterByAll(category: String, subject: String, subChapter: String): List<Concept> = 
        conceptDao.filterByAll(category, subject, subChapter)

    suspend fun getSubjectsByCategory(category: String): List<String> = conceptDao.getSubjectsByCategory(category)

    suspend fun getSubChaptersByCategoryAndSubject(category: String, subject: String): List<String> = 
        conceptDao.getSubChaptersByCategoryAndSubject(category, subject)

    fun saveImageToFile(base64Image: String?): String? {
        return base64Image?.let {
            try {
                val imagesDir = File(context.filesDir, "concept_images")
                if (!imagesDir.exists()) {
                    imagesDir.mkdirs()
                }

                val fileName = "concept_${System.currentTimeMillis()}.jpg"
                val file = File(imagesDir, fileName)
                file.writeBytes(android.util.Base64.decode(it, android.util.Base64.NO_WRAP))
                file.absolutePath
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }

    fun encodeImageToBase64(imagePath: String?): String? {
        return imagePath?.let { path ->
            try {
                val file = File(path)
                if (file.exists()) {
                    val bytes = file.readBytes()
                    android.util.Base64.encodeToString(bytes, android.util.Base64.NO_WRAP)
                } else {
                    null
                }
            } catch (e: Exception) {
                e.printStackTrace()
                null
            }
        }
    }

    fun saveImageFromBase64IfNeeded(concept: Concept): Concept {
        return if (concept.imageBase64 != null && concept.imagePath == null) {
            val newPath = saveImageToFile(concept.imageBase64)
            concept.copy(imagePath = newPath)
        } else {
            concept
        }
    }
}
