package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.domain.model.Article
import com.dailyread.app.data.local.database.entities.toEntity
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class DeleteArticleUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository
) {
    suspend operator fun invoke(article: Article) {
        checkInRepository.deleteCheckInsByContent(article.id)
        contentRepository.deleteContent(article.toEntity())
    }
}
