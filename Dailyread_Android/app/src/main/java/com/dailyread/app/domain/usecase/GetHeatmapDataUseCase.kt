package com.dailyread.app.domain.usecase
import com.dailyread.app.data.repository.CheckInRepository
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class GetHeatmapDataUseCase @Inject constructor(
    private val checkInRepository: CheckInRepository
) {
    suspend operator fun invoke(year: Int): Map<String, Int> {
        return try {
            val checkIns = checkInRepository.getCheckInDataByYear(year.toString())
            checkIns.groupBy { it.date }.mapValues { it.value.size }
        } catch (e: Exception) {
            e.printStackTrace()
            emptyMap()
        }
    }
}