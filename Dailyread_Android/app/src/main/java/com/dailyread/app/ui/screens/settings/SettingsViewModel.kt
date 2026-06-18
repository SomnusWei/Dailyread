package com.dailyread.app.ui.screens.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.dailyread.app.domain.usecase.ExportDataUseCase
import com.dailyread.app.domain.usecase.ExportType
import com.dailyread.app.domain.usecase.ImportDataUseCase
import com.dailyread.app.domain.usecase.ImportDataType
import com.dailyread.app.domain.usecase.ResetTodayTasksUseCase
import com.dailyread.app.domain.usecase.WebDavSyncUseCase
import com.dailyread.app.domain.usecase.AutoSyncManager
import com.dailyread.app.data.repository.ConfigRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class SettingsUiState(
    val dailyMinutes: Int = 20,
    val targetCheckRate: Float = 30.0f,
    val keepScreenOn: Boolean = false,
    val showToast: String? = null,
    val isTasksLocked: Boolean = false,
    val webdavEnabled: Boolean = false,
    val webdavServerUrl: String = "",
    val webdavUsername: String = "",
    val webdavPassword: String = "",
    val webdavRemotePath: String = "/DailyRead",
    val lastSyncTime: String? = null,
    val isSyncing: Boolean = false,
    val showConflictDialog: Boolean = false,
    val currentConflict: WebDavSyncUseCase.SyncConflict? = null,
    val autoSyncWebDav: Boolean = false,
    val syncArticlesEnabled: Boolean = true,
    val syncAcupointsEnabled: Boolean = true,
    val syncConceptsEnabled: Boolean = true
)

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val exportDataUseCase: ExportDataUseCase,
    private val importDataUseCase: ImportDataUseCase,
    private val resetTodayTasksUseCase: ResetTodayTasksUseCase,
    private val webDavSyncUseCase: WebDavSyncUseCase,
    private val configRepository: ConfigRepository,
    private val autoSyncManager: AutoSyncManager
) : ViewModel() {

    private val _uiState = MutableStateFlow(SettingsUiState())
    val uiState: StateFlow<SettingsUiState> = _uiState.asStateFlow()

    init {
        loadConfig()
    }

    private fun loadConfig() {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                _uiState.update {
                    it.copy(
                        dailyMinutes = config.dailyMinutes,
                        targetCheckRate = config.targetCheckRate,
                        keepScreenOn = config.keepScreenOn,
                        webdavEnabled = config.webdavEnabled,
                        webdavServerUrl = config.webdavServerUrl,
                        webdavUsername = config.webdavUsername,
                        webdavPassword = config.webdavPassword,
                        webdavRemotePath = config.webdavRemotePath,
                        lastSyncTime = config.lastSyncTime,
                        autoSyncWebDav = config.autoSyncWebDav,
                        syncArticlesEnabled = config.syncArticlesEnabled,
                        syncAcupointsEnabled = config.syncAcupointsEnabled,
                        syncConceptsEnabled = config.syncConceptsEnabled
                    )
                }
                checkTasksLockStatus()
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }
    
    private fun checkTasksLockStatus() {
        viewModelScope.launch {
            try {
                val isLocked = configRepository.isTodayTasksLocked()
                _uiState.update { it.copy(isTasksLocked = isLocked) }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(isTasksLocked = false) }
            }
        }
    }

    fun updateDailyMinutes(minutes: Int) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(dailyMinutes = minutes)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(dailyMinutes = minutes) }
                runCatching { autoSyncManager.triggerAutoSync() }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "更新失败: ${e.message}") }
            }
        }
    }

    fun updateTargetCheckRate(rate: Float) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(targetCheckRate = rate)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(targetCheckRate = rate) }
                runCatching { autoSyncManager.triggerAutoSync() }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "更新失败: ${e.message}") }
            }
        }
    }

    fun updateKeepScreenOn(keepOn: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(keepScreenOn = keepOn)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(keepScreenOn = keepOn) }
                runCatching { autoSyncManager.triggerAutoSync() }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "更新失败: ${e.message}") }
            }
        }
    }

    fun updateWebDavConfig(
        serverUrl: String,
        username: String,
        password: String,
        remotePath: String
    ) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(
                    webdavServerUrl = serverUrl,
                    webdavUsername = username,
                    webdavPassword = password,
                    webdavRemotePath = remotePath
                )
                configRepository.updateConfig(updatedConfig)
                _uiState.update {
                    it.copy(
                        webdavServerUrl = serverUrl,
                        webdavUsername = username,
                        webdavPassword = password,
                        webdavRemotePath = remotePath
                    )
                }
                runCatching { autoSyncManager.triggerAutoSync() }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "保存配置失败: ${e.message}") }
            }
        }
    }

    fun toggleWebDavEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(webdavEnabled = enabled)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(webdavEnabled = enabled) }
                runCatching { autoSyncManager.triggerAutoSync() }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "设置失败: ${e.message}") }
            }
        }
    }

    fun updateAutoSyncWebDav(enabled: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(autoSyncWebDav = enabled)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(autoSyncWebDav = enabled) }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "设置失败: ${e.message}") }
            }
        }
    }

    fun updateSyncArticlesEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(syncArticlesEnabled = enabled)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(syncArticlesEnabled = enabled) }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "设置失败: ${e.message}") }
            }
        }
    }

    fun updateSyncAcupointsEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(syncAcupointsEnabled = enabled)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(syncAcupointsEnabled = enabled) }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "设置失败: ${e.message}") }
            }
        }
    }

    fun updateSyncConceptsEnabled(enabled: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val updatedConfig = config.copy(syncConceptsEnabled = enabled)
                configRepository.updateConfig(updatedConfig)
                _uiState.update { it.copy(syncConceptsEnabled = enabled) }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "设置失败: ${e.message}") }
            }
        }
    }

    fun testWebDavConnection() {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                _uiState.update { it.copy(isSyncing = true) }

                val result = webDavSyncUseCase.testConnection(config)

                _uiState.update { it.copy(isSyncing = false) }

                if (result.success) {
                    _uiState.update { it.copy(showToast = "连接成功！") }
                } else {
                    _uiState.update { it.copy(showToast = "连接失败: ${result.errorMessage}") }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(isSyncing = false, showToast = "连接失败: ${e.message}") }
            }
        }
    }

    fun syncFromCloud() {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                _uiState.update { it.copy(isSyncing = true) }

                val result = webDavSyncUseCase.syncFromRemote(config)

                _uiState.update { it.copy(isSyncing = false) }

                if (result.success) {
                    if (result.conflicts.isNotEmpty()) {
                        _uiState.update {
                            it.copy(
                                showConflictDialog = true,
                                currentConflict = result.conflicts.first()
                            )
                        }
                    } else {
                        val message = buildString {
                            append("同步成功！\n")
                            if (result.downloadedArticles > 0) append("下载文章: ${result.downloadedArticles}\n")
                            if (result.downloadedCheckIns > 0) append("下载打卡: ${result.downloadedCheckIns}\n")
                            if (result.downloadedAcupoints > 0) append("下载穴位: ${result.downloadedAcupoints}\n")
                            if (result.downloadedConcepts > 0) append("下载概念: ${result.downloadedConcepts}")
                        }
                        _uiState.update { it.copy(showToast = message, lastSyncTime = config.lastSyncTime) }
                    }
                } else {
                    _uiState.update { it.copy(showToast = "同步失败: ${result.errorMessage}") }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(isSyncing = false, showToast = "同步失败: ${e.message}") }
            }
        }
    }

    fun syncToCloud() {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                _uiState.update { it.copy(isSyncing = true) }

                val result = webDavSyncUseCase.syncToRemote(config)

                _uiState.update { it.copy(isSyncing = false) }

                if (result.success) {
                    val message = buildString {
                        append("上传成功！\n")
                        if (result.uploadedArticles > 0) append("上传文章: ${result.uploadedArticles}\n")
                        if (result.uploadedCheckIns > 0) append("上传打卡: ${result.uploadedCheckIns}\n")
                        if (result.uploadedAcupoints > 0) append("上传穴位: ${result.uploadedAcupoints}\n")
                        if (result.uploadedConcepts > 0) append("上传概念: ${result.uploadedConcepts}")
                    }
                    _uiState.update {
                        it.copy(
                            showToast = message,
                            lastSyncTime = config.lastSyncTime
                        )
                    }
                } else {
                    _uiState.update { it.copy(showToast = "上传失败: ${result.errorMessage}") }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(isSyncing = false, showToast = "上传失败: ${e.message}") }
            }
        }
    }

    fun resolveConflict(useLocal: Boolean) {
        viewModelScope.launch {
            try {
                val config = configRepository.getConfigOnce()
                val conflict = _uiState.value.currentConflict

                if (conflict != null) {
                    _uiState.update { it.copy(isSyncing = true, showConflictDialog = false) }

                    val result = webDavSyncUseCase.resolveConflict(config, conflict, useLocal)

                    _uiState.update { it.copy(isSyncing = false) }

                    if (result.success) {
                        _uiState.update {
                            it.copy(
                                showToast = "冲突已解决",
                                lastSyncTime = config.lastSyncTime
                            )
                        }
                    } else {
                        _uiState.update { it.copy(showToast = "解决冲突失败: ${result.errorMessage}") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(isSyncing = false, showToast = "解决冲突失败: ${e.message}") }
            }
        }
    }

    fun dismissConflictDialog() {
        _uiState.update {
            it.copy(
                showConflictDialog = false,
                currentConflict = null
            )
        }
    }

    fun exportData() {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase(ExportType.ALL)) {
                    is ExportDataUseCase.Result.Success -> {
                        val typeStr = when (result.exportType) {
                            ExportType.ALL -> "全部"
                            ExportType.ARTICLES_ONLY -> "文章"
                            ExportType.ACUPOINTS_ONLY -> "穴位"
                            ExportType.CONCEPTS_ONLY -> "概念"
                        }
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun exportDataWithPath(exportType: ExportType, savePath: String) {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase(exportType, savePath)) {
                    is ExportDataUseCase.Result.Success -> {
                        val typeStr = when (result.exportType) {
                            ExportType.ALL -> "全部"
                            ExportType.ARTICLES_ONLY -> "文章"
                            ExportType.ACUPOINTS_ONLY -> "穴位"
                            ExportType.CONCEPTS_ONLY -> "概念"
                        }
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun exportDataWithUri(exportType: ExportType, uri: android.net.Uri) {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase.exportToUri(exportType, uri)) {
                    is ExportDataUseCase.Result.Success -> {
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun exportArticlesOnly() {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase(ExportType.ARTICLES_ONLY)) {
                    is ExportDataUseCase.Result.Success -> {
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun exportAcupointsOnly() {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase(ExportType.ACUPOINTS_ONLY)) {
                    is ExportDataUseCase.Result.Success -> {
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun exportConceptsOnly() {
        viewModelScope.launch {
            try {
                when (val result = exportDataUseCase(ExportType.CONCEPTS_ONLY)) {
                    is ExportDataUseCase.Result.Success -> {
                        _uiState.update { it.copy(showToast = "导出成功！\n已保存到: ${result.filePath}") }
                    }
                    is ExportDataUseCase.Result.Error -> {
                        _uiState.update { it.copy(showToast = "导出失败，请检查存储权限") }
                    }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导出失败: ${e.message}") }
            }
        }
    }

    fun importData(filePath: String) {
        viewModelScope.launch {
            try {
                val result = importDataUseCase(filePath)
                if (result.success) {
                    val message = buildString {
                        when (result.dataType) {
                            ImportDataType.ARTICLES -> {
                                if (result.newArticles > 0) append("新增文章: ${result.newArticles}\n")
                                if (result.updatedArticles > 0) append("更新文章: ${result.updatedArticles}\n")
                                if (result.skippedArticles > 0) append("跳过文章: ${result.skippedArticles}\n")
                                if (result.newCheckIns > 0) append("新增打卡: ${result.newCheckIns}\n")
                                if (result.skippedCheckIns > 0) append("跳过打卡: ${result.skippedCheckIns}")
                            }
                            ImportDataType.ACUPOINTS -> {
                                if (result.newAcupoints > 0) append("新增穴位: ${result.newAcupoints}\n")
                                if (result.skippedAcupoints > 0) append("跳过穴位: ${result.skippedAcupoints}")
                            }
                            ImportDataType.CONCEPTS -> {
                                if (result.newConcepts > 0) append("新增概念: ${result.newConcepts}\n")
                                if (result.skippedConcepts > 0) append("跳过概念: ${result.skippedConcepts}")
                            }
                            ImportDataType.ALL -> {
                                if (result.newArticles > 0) append("新增文章: ${result.newArticles}\n")
                                if (result.updatedArticles > 0) append("更新文章: ${result.updatedArticles}\n")
                                if (result.newCheckIns > 0) append("新增打卡: ${result.newCheckIns}\n")
                                if (result.newAcupoints > 0) append("新增穴位: ${result.newAcupoints}\n")
                                if (result.skippedAcupoints > 0) append("跳过穴位: ${result.skippedAcupoints}\n")
                                if (result.newConcepts > 0) append("新增概念: ${result.newConcepts}\n")
                                if (result.skippedConcepts > 0) append("跳过概念: ${result.skippedConcepts}")
                            }
                            else -> {}
                        }
                        if (isEmpty()) append("无变化")
                    }
                    _uiState.update { it.copy(showToast = message) }
                } else {
                    _uiState.update { it.copy(showToast = "导入失败: ${result.errorMessage}") }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "导入失败: ${e.message}") }
            }
        }
    }

    fun clearToast() {
        _uiState.update { it.copy(showToast = null) }
    }
    
    fun resetTodayTasks() {
        viewModelScope.launch {
            try {
                val success = resetTodayTasksUseCase()
                if (success) {
                    _uiState.update { 
                        it.copy(
                            showToast = "今日任务已重置",
                            isTasksLocked = false
                        ) 
                    }
                } else {
                    _uiState.update { it.copy(showToast = "重置失败，请重试") }
                }
            } catch (e: Exception) {
                e.printStackTrace()
                _uiState.update { it.copy(showToast = "重置失败: ${e.message}") }
            }
        }
    }
}
