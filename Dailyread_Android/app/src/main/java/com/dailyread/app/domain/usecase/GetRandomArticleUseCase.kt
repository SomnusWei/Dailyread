package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.local.database.entities.toDomainModel
import com.dailyread.app.domain.model.Article
import kotlinx.coroutines.flow.firstOrNull
import javax.inject.Inject
import javax.inject.Singleton
import kotlin.random.Random

@Singleton
class GetRandomArticleUseCase @Inject constructor(
    private val contentRepository: ContentRepository
) {
    suspend operator fun invoke(): Article? {
        return try {
            val allContents = contentRepository.getAllContents().firstOrNull() ?: return null
            val pausedArticles = allContents
                .filter { !it.isReading }
                .map { it.toDomainModel() }
            
            if (pausedArticles.isEmpty()) return null
            
            val randomIndex = Random.nextInt(pausedArticles.size)
            pausedArticles[randomIndex]
        } catch (e: Exception) {
            e.printStackTrace()
            null
        }
    }
}
