package com.dailyread.app.data.repository
import com.dailyread.app.data.local.database.dao.ConfigDao
import com.dailyread.app.data.local.database.entities.Config
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.firstOrNull
import java.time.LocalDate
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ConfigRepository @Inject constructor(
    private val configDao: ConfigDao
) {
    fun getConfig(): Flow<Config?> = configDao.getConfig()

    suspend fun getConfigOnce(): Config {
        return configDao.getConfigOnce() ?: Config().also { configDao.insertConfig(it) }
    }

    suspend fun insertConfig(config: Config) = configDao.insertConfig(config)

    suspend fun updateConfig(config: Config) = configDao.updateConfig(config)

    suspend fun lockTodayTasks() {
        val config = getConfigOnce()
        val today = LocalDate.now().toString()
        updateConfig(config.copy(tasksLocked = true, tasksLockedDate = today))
    }

    suspend fun unlockTodayTasks() {
        val config = getConfigOnce()
        updateConfig(config.copy(tasksLocked = false, tasksLockedDate = null))
    }

    suspend fun isTodayTasksLocked(): Boolean {
        val config = getConfigOnce()
        val today = LocalDate.now().toString()
        
        // 检查是否需要自动解锁（跨天）
        if (config.tasksLocked && config.tasksLockedDate != today) {
            unlockTodayTasks()
            return false
        }
        
        return config.tasksLocked
    }
}