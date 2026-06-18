package com.dailyread.app.domain.usecase
import com.dailyread.app.data.local.database.entities.ContentCheckIn
import com.dailyread.app.data.repository.CheckInRepository
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CheckInArticleUseCase @Inject constructor(
    private val checkInRepository: CheckInRepository
) {
    sealed class Result {
        object Success : Result()
        object AlreadyCheckedIn : Result()
        object Error : Result()
    }

    suspend operator fun invoke(contentId: Long): Result {
        val today = LocalDate.now().toString()
        val checkIns = checkInRepository.getCheckInDataByYear(today.substring(0, 4))
            .filter { it.contentId == contentId && it.date == today }

        if (checkIns.isNotEmpty()) {
            return Result.AlreadyCheckedIn
        }

        return try {
            checkInRepository.insertCheckIn(ContentCheckIn(contentId = contentId, date = today))
            Result.Success
        } catch (e: Exception) {
            Result.Error
        }
    }
}
