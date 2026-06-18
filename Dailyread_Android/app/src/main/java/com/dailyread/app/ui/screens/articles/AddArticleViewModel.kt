package com.dailyread.app.ui.screens.articles

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.model.Article
import com.dailyread.app.domain.usecase.AddArticleUseCase
import com.dailyread.app.domain.usecase.UpdateArticleUseCase
import com.dailyread.app.domain.usecase.AutoSyncManager
import com.dailyread.app.data.repository.ContentRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import javax.inject.Inject

data class AddArticleUiState(
    val title: String = "",
    val content: String = "",
    val isReading: Boolean = true,
    val isRequired: Boolean = false,
    val requiredDays: String = "",
    val navigateBack: Boolean = false
)

@HiltViewModel
class AddArticleViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
    private val addArticleUseCase: AddArticleUseCase,
    private val updateArticleUseCase: UpdateArticleUseCase,
    private val autoSyncManager: AutoSyncManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(AddArticleUiState())
    val uiState: StateFlow<AddArticleUiState> = _uiState.asStateFlow()

    private var currentArticleId: Long? = null

    fun loadArticle(articleId: Long) {
        viewModelScope.launch {
            currentArticleId = articleId
            val content = contentRepository.getContentById(articleId)
            content?.let {
                _uiState.update {
                    it.copy(
                        title = content.title,
                        content = content.content,
                        isReading = content.isReading,
                        isRequired = content.isRequired,
                        requiredDays = content.requiredDays
                    )
                }
            }
        }
    }

    fun saveArticle(
        title: String,
        content: String,
        chineseChars: Int,
        isReading: Boolean,
        isRequired: Boolean = false,
        requiredDays: String = ""
    ) {
        viewModelScope.launch {
            if (currentArticleId != null) {
                val existingArticle = contentRepository.getContentById(currentArticleId!!)
                existingArticle?.let {
                    val updatedArticle = Article(
                        id = it.id,
                        title = title,
                        content = content,
                        contentHtml = it.contentHtml,
                        chineseChars = chineseChars,
                        fontFamily = it.fontFamily,
                        fontSize = it.fontSize,
                        fontColor = it.fontColor,
                        isBold = it.isBold,
                        isReading = isReading,
                        isRequired = isRequired,
                        requiredDays = requiredDays,
                        createTime = it.createTime
                    )
                    updateArticleUseCase(updatedArticle)
                }
            } else {
                val article = Article(
                    id = 0L,
                    title = title,
                    content = content,
                    contentHtml = null,
                    chineseChars = chineseChars,
                    fontFamily = "default",
                    fontSize = 16,
                    fontColor = "#000000",
                    isBold = false,
                    isReading = isReading,
                    isRequired = isRequired,
                    requiredDays = requiredDays,
                    createTime = LocalDateTime.now().toString()
                )
                addArticleUseCase(article)
            }
            autoSyncManager.triggerAutoSync()
            _uiState.update { it.copy(navigateBack = true) }
        }
    }
}
