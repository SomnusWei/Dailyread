package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.domain.model.Article
import com.dailyread.app.data.local.database.entities.toEntity
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class UpdateArticleUseCase @Inject constructor(
    private val contentRepository: ContentRepository
) {
    suspend operator fun invoke(article: Article) {
        contentRepository.updateContent(article.toEntity())
    }
}
