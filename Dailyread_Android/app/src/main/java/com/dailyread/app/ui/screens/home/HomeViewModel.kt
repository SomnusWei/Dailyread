package com.dailyread.app.ui.screens.home
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.model.Article
import com.dailyread.app.domain.usecase.GetHeatmapDataUseCase
import com.dailyread.app.domain.usecase.GetTodayTasksUseCase
import com.dailyread.app.data.repository.CheckInRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

data class HomeUiState(
    val todayTasks: List<Article> = emptyList(),
    val checkedInArticles: Set<Long> = emptySet(),
    val heatmapData: Map<String, Int> = emptyMap(),
    val totalWords: Int = 0
)

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getTodayTasksUseCase: GetTodayTasksUseCase,
    private val getHeatmapDataUseCase: GetHeatmapDataUseCase,
    private val checkInRepository: CheckInRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(HomeUiState())
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    init {
        loadData()
    }

    fun loadData() {
        viewModelScope.launch {
            try {
                val today = LocalDate.now()
                val tasks = try {
                    getTodayTasksUseCase()
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyList()
                }

                val yearPrefix = today.year.toString()
                val checkIns = try {
                    checkInRepository.getCheckInDataByYear(yearPrefix)
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyList()
                }
                val todayCheckIns = checkIns.filter { it.date == today.toString() }
                val checkedInIds = todayCheckIns.map { it.contentId }.toSet()

                val heatmapData = try {
                    getHeatmapDataUseCase(today.year)
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyMap()
                }

                _uiState.update {
                    it.copy(
                        todayTasks = tasks,
                        checkedInArticles = checkedInIds,
                        heatmapData = heatmapData,
                        totalWords = tasks.filter { !it.isRequired }.sumOf { article -> article.chineseChars }
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}