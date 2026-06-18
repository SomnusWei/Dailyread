package com.dailyread.app.ui.screens.articles

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.data.local.database.entities.toDomainModel
import com.dailyread.app.data.local.database.entities.toEntity
import com.dailyread.app.domain.model.Article
import com.dailyread.app.domain.usecase.DeleteArticleUseCase
import com.dailyread.app.domain.usecase.BackFillCheckInUseCase
import com.dailyread.app.domain.usecase.CancelCheckInUseCase
import com.dailyread.app.domain.usecase.AutoSyncManager
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.CheckInRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import javax.inject.Inject

data class ArticlesUiState(
    val articles: List<ArticleWithCheckRate> = emptyList(),
    val selectedArticleIds: Set<Long> = emptySet(),
    val isSelectionMode: Boolean = false
)

data class ArticleWithCheckRate(
    val article: Article,
    val checkRate: Float = 0f,
    val checkInDates: Set<String> = emptySet()
)

@HiltViewModel
class ArticlesViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
    private val deleteArticleUseCase: DeleteArticleUseCase,
    private val backFillCheckInUseCase: BackFillCheckInUseCase,
    private val cancelCheckInUseCase: CancelCheckInUseCase,
    private val checkInRepository: CheckInRepository,
    private val autoSyncManager: AutoSyncManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(ArticlesUiState())
    val uiState: StateFlow<ArticlesUiState> = _uiState.asStateFlow()

    fun loadArticles() {
        viewModelScope.launch {
            try {
                contentRepository.getAllContents().collect { contents ->
                    val today = LocalDate.now()
                    val yearPrefix = today.year.toString()
                    val allCheckIns = try {
                        checkInRepository.getCheckInDataByYear(yearPrefix)
                    } catch (e: Exception) {
                        e.printStackTrace()
                        emptyList()
                    }
                    
                    val articles = contents.map { content ->
                        val rate = try {
                            calculateCheckRate(content.id, today, allCheckIns)
                        } catch (e: Exception) {
                            e.printStackTrace()
                            0f
                        }
                        val checkInDates = allCheckIns
                            .filter { it.contentId == content.id }
                            .map { it.date }
                            .toSet()
                        ArticleWithCheckRate(
                            article = content.toDomainModel(),
                            checkRate = rate,
                            checkInDates = checkInDates
                        )
                    }
                    _uiState.update { it.copy(articles = articles) }
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun deleteArticle(article: Article) {
        viewModelScope.launch {
            deleteArticleUseCase(article)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun toggleArticleSelection(articleId: Long) {
        _uiState.update { currentState ->
            val newSelectedIds = currentState.selectedArticleIds.toMutableSet().apply {
                if (contains(articleId)) remove(articleId) else add(articleId)
            }.toSet()
            val isInSelectionMode = newSelectedIds.isNotEmpty()
            currentState.copy(
                selectedArticleIds = newSelectedIds,
                isSelectionMode = isInSelectionMode
            )
        }
    }

    fun selectAllArticles() {
        _uiState.update { currentState ->
            val allArticleIds = currentState.articles.map { it.article.id }.toSet()
            currentState.copy(
                selectedArticleIds = allArticleIds,
                isSelectionMode = allArticleIds.isNotEmpty()
            )
        }
    }

    fun clearSelection() {
        _uiState.update { currentState ->
            currentState.copy(
                selectedArticleIds = emptySet(),
                isSelectionMode = false
            )
        }
    }

    fun deleteSelectedArticles() {
        viewModelScope.launch {
            val selectedArticles = _uiState.value.articles
                .filter { it.article.id in _uiState.value.selectedArticleIds }
                .map { it.article }
            selectedArticles.forEach { article ->
                deleteArticleUseCase(article)
            }
            clearSelection()
            autoSyncManager.triggerAutoSync()
        }
    }

    fun toggleReading(article: Article) {
        viewModelScope.launch {
            val entity = article.toEntity().copy(isReading = !article.isReading)
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun toggleRequired(article: Article) {
        viewModelScope.launch {
            val entity = article.toEntity().copy(isRequired = !article.isRequired, requiredDays = "")
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun updateRequiredDays(article: Article, days: String) {
        viewModelScope.launch {
            val newIsRequired = days.isNotEmpty()
            val entity = article.toEntity().copy(
                isRequired = newIsRequired,
                requiredDays = days
            )
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun toggleIndependentCheckRate(article: Article) {
        viewModelScope.launch {
            val entity = article.toEntity().copy(
                useIndependentCheckRate = !article.useIndependentCheckRate
            )
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun updateIndependentCheckRate(article: Article, rate: Float) {
        viewModelScope.launch {
            val entity = article.toEntity().copy(
                independentCheckRate = rate
            )
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun updateIndependentCheckRateWithEnabled(article: Article, enabled: Boolean, rate: Float) {
        viewModelScope.launch {
            val entity = article.toEntity().copy(
                useIndependentCheckRate = enabled,
                independentCheckRate = rate
            )
            contentRepository.updateContent(entity)
            autoSyncManager.triggerAutoSync()
        }
    }

    fun backFillCheckIn(articleId: Long, dates: List<String>) {
        viewModelScope.launch {
            backFillCheckInUseCase(articleId, dates)
            loadArticles() // 重新加载文章数据以更新完成率
            autoSyncManager.triggerAutoSync()
        }
    }

    fun cancelCheckIn(articleId: Long, dates: List<String>) {
        viewModelScope.launch {
            cancelCheckInUseCase(articleId, dates)
            loadArticles() // 重新加载文章数据以更新完成率
            autoSyncManager.triggerAutoSync()
        }
    }

    private fun calculateCheckRate(
        contentId: Long,
        today: LocalDate,
        allCheckIns: List<com.dailyread.app.data.local.database.entities.ContentCheckIn>
    ): Float {
        val year = today.year
        val month = today.monthValue
        
        val checkIns = allCheckIns.filter { 
            it.contentId == contentId && it.date.startsWith("$year-${String.format("%02d", month)}")
        }
        
        val daysInMonth = YearMonth.of(year, month).lengthOfMonth()
        val totalDays = if (year == today.year && month == today.monthValue) {
            today.dayOfMonth
        } else {
            daysInMonth
        }
        
        return if (totalDays > 0) (checkIns.size.toFloat() / totalDays.toFloat() * 100f) else 0f
    }
}
