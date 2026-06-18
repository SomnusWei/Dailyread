package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.ConfigRepository
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ResetTodayTasksUseCase @Inject constructor(
    private val configRepository: ConfigRepository
) {
    suspend operator fun invoke(): Boolean {
        return try {
            val config = configRepository.getConfigOnce()
            configRepository.updateConfig(
                config.copy(
                    tasksLocked = false,
                    tasksLockedDate = null,
                    todayTasks = null
                )
            )
            true
        } catch (e: Exception) {
            false
        }
    }
}
