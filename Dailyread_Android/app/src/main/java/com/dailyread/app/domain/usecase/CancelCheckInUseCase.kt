package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.CheckInRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class CancelCheckInUseCase @Inject constructor(
    private val checkInRepository: CheckInRepository
) {
    suspend operator fun invoke(contentId: Long, dates: List<String>) {
        dates.forEach { date ->
            checkInRepository.deleteCheckInByDate(contentId, date)
        }
    }
}
