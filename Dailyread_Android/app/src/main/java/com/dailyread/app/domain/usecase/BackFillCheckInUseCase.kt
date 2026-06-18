package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.local.database.entities.ContentCheckIn
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class BackFillCheckInUseCase @Inject constructor(
    private val checkInRepository: CheckInRepository
) {
    suspend operator fun invoke(contentId: Long, dates: List<String>) {
        val checkIns = dates.map { date ->
            ContentCheckIn(contentId = contentId, date = date)
        }
        checkInRepository.insertAllCheckIns(checkIns)
    }
}
