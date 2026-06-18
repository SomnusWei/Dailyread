package com.dailyread.app.ui.screens.stats

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.usecase.GetHeatmapDataUseCase
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.CheckInRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.time.LocalDate
import javax.inject.Inject

data class StatsUiState(
    val heatmapData: Map<String, Int> = emptyMap(),
    val totalArticles: Int = 0,
    val totalCheckIns: Int = 0
)

@HiltViewModel
class StatsViewModel @Inject constructor(
    private val getHeatmapDataUseCase: GetHeatmapDataUseCase,
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(StatsUiState())
    val uiState: StateFlow<StatsUiState> = _uiState.asStateFlow()

    fun loadData() {
        viewModelScope.launch {
            try {
                val year = LocalDate.now().year
                val heatmapData = try {
                    getHeatmapDataUseCase(year)
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyMap()
                }
                val articles = try {
                    contentRepository.getAllContentsOnce()
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyList()
                }
                val checkIns = try {
                    checkInRepository.getAllCheckInRecords()
                } catch (e: Exception) {
                    e.printStackTrace()
                    emptyList()
                }

                _uiState.update {
                    it.copy(
                        heatmapData = heatmapData,
                        totalArticles = articles.size,
                        totalCheckIns = checkIns.size
                    )
                }
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
}
