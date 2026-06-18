package com.dailyread.app.ui.screens.reader
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.model.Article
import com.dailyread.app.domain.usecase.CheckInArticleUseCase
import com.dailyread.app.domain.usecase.AutoSyncManager
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.CheckInRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import java.time.LocalDate
import javax.inject.Inject

data class ReaderUiState(
    val article: Article? = null,
    val isCheckedIn: Boolean = false,
    val showToast: String? = null,
    val fontSize: Int = 26, // 默认字体大小26sp
    val readingTimeSeconds: Int = 0 // 阅读时间（秒）
)

@HiltViewModel
class ReaderViewModel @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val checkInArticleUseCase: CheckInArticleUseCase,
    private val autoSyncManager: AutoSyncManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(ReaderUiState())
    val uiState: StateFlow<ReaderUiState> = _uiState.asStateFlow()

    private var timerJob: Job? = null

    fun loadArticle(articleId: Long) {
        viewModelScope.launch {
            try {
                val content = contentRepository.getContentById(articleId)
                val article = content?.let {
                    Article(
                        id = it.id,
                        title = it.title,
                        content = it.content,
                        contentHtml = it.contentHtml,
                        chineseChars = it.chineseChars,
                        fontFamily = it.fontFamily,
                        fontSize = it.fontSize,
                        fontColor = it.fontColor,
                        isBold = it.isBold,
                        isReading = it.isReading,
                        createTime = it.createTime
                    )
                }

                val today = LocalDate.now().toString()
                val checkIns = try {
                    checkInRepository.getCheckInDataByYear(today.substring(0, 4))
                        .filter { it.contentId == articleId && it.date == today }
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyList()
                }
                val isCheckedIn = checkIns.isNotEmpty()

                _uiState.update {
                    it.copy(
                        article = article, 
                        isCheckedIn = isCheckedIn,
                        fontSize = 26, // 强制使用26作为默认字体大小
                        readingTimeSeconds = 0 // 重置计时器
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    fun startTimer() {
        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            while (isActive) {
                delay(1000)
                _uiState.update { it.copy(readingTimeSeconds = it.readingTimeSeconds + 1) }
            }
        }
    }

    fun stopTimer() {
        timerJob?.cancel()
        timerJob = null
    }

    override fun onCleared() {
        super.onCleared()
        timerJob?.cancel()
    }

    fun checkIn() {
        viewModelScope.launch {
            _uiState.value.article?.let { article ->
                when (val result = checkInArticleUseCase(article.id)) {
                    CheckInArticleUseCase.Result.Success -> {
                        _uiState.update {
                            it.copy(
                                isCheckedIn = true,
                                showToast = "打卡成功！"
                            )
                        }
                        autoSyncManager.triggerAutoSync()
                    }
                    CheckInArticleUseCase.Result.AlreadyCheckedIn -> {
                        _uiState.update {
                            it.copy(showToast = "今日已打卡")
                        }
                    }
                    CheckInArticleUseCase.Result.Error -> {
                        _uiState.update {
                            it.copy(showToast = "打卡失败")
                        }
                    }
                }
            }
        }
    }

    fun increaseFontSize() {
        _uiState.update {
            val newSize = (it.fontSize + 2).coerceAtMost(32) // 最大32
            it.copy(fontSize = newSize)
        }
    }

    fun decreaseFontSize() {
        _uiState.update {
            val newSize = (it.fontSize - 2).coerceAtLeast(12) // 最小12
            it.copy(fontSize = newSize)
        }
    }

    fun resetFontSize() {
        _uiState.update {
            it.copy(fontSize = 26) // 重置为默认字体
        }
    }

    fun clearToast() {
        _uiState.update { it.copy(showToast = null) }
    }
}