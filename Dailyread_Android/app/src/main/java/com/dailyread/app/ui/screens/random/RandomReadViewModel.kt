package com.dailyread.app.ui.screens.random

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.model.Article
import com.dailyread.app.domain.usecase.GetRandomArticleUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

data class RandomReadUiState(
    val article: Article? = null,
    val hasArticle: Boolean = false,
    val showToast: String? = null
)

@HiltViewModel
class RandomReadViewModel @Inject constructor(
    private val getRandomArticleUseCase: GetRandomArticleUseCase
) : ViewModel() {

    private val _uiState = MutableStateFlow(RandomReadUiState())
    val uiState: StateFlow<RandomReadUiState> = _uiState.asStateFlow()

    init {
        loadRandomArticle()
    }

    fun loadRandomArticle() {
        viewModelScope.launch {
            try {
                val article = getRandomArticleUseCase()
                if (article != null) {
                    _uiState.update {
                        it.copy(article = article, hasArticle = true)
                    }
                } else {
                    _uiState.update {
                        it.copy(
                            hasArticle = false,
                            showToast = "暂无可阅读的文章"
                        )
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update {
                    it.copy(
                        hasArticle = false,
                        showToast = "加载失败，请重试"
                    )
                }
            }
        }
    }

    fun clearToast() {
        _uiState.update { it.copy(showToast = null) }
    }
}
