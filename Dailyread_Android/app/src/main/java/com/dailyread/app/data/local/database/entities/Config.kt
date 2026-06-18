package com.dailyread.app.data.local.database.entities
import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "config")
data class Config(
    @PrimaryKey
    val id: Int = 1,
    val dailyMinutes: Int = 20,
    val theme: String = "system",
    val targetCheckRate: Float = 30.0f,
    val todayTasks: String? = null,
    val tasksLocked: Boolean = false,
    val tasksLockedDate: String? = null,
    val keepScreenOn: Boolean = false,
    val webdavEnabled: Boolean = false,
    val webdavServerUrl: String = "",
    val webdavUsername: String = "",
    val webdavPassword: String = "",
    val webdavRemotePath: String = "/DailyRead",
    val lastSyncTime: String? = null,
    val autoSyncWebDav: Boolean = false,
    val yesterdayLongArticleIds: String = "", // JSON数组，如 "[1,2,3]"
    val syncArticlesEnabled: Boolean = true,
    val syncAcupointsEnabled: Boolean = true,
    val syncConceptsEnabled: Boolean = true
)
