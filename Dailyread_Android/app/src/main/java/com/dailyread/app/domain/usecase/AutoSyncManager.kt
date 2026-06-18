package com.dailyread.app.domain.usecase

import com.dailyread.app.data.repository.ConfigRepository
import dagger.Lazy
import com.dailyread.app.data.repository.ContentRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AutoSyncManager @Inject constructor(
    private val configRepository: ConfigRepository,
    private val webDavSyncUseCaseLazy: dagger.Lazy<WebDavSyncUseCase>
) {
    private val scope = CoroutineScope(Dispatchers.IO + Job())
    private var syncJob: Job? = null
    private val SYNC_DELAY_MS = 2000L

    private val webDavSyncUseCase: WebDavSyncUseCase
        get() = webDavSyncUseCaseLazy.get()

    fun triggerAutoSync() {
        try {
            syncJob?.cancel()
            syncJob = scope.launch {
                delay(SYNC_DELAY_MS)
                performSync()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private suspend fun performSync() {
        try {
            val config = configRepository.getConfigOnce()
            if (config.webdavEnabled && config.autoSyncWebDav) {
                webDavSyncUseCase.syncToRemote(config)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
