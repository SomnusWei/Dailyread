package com.dailyread.app.data.repository

import com.dailyread.app.data.local.database.dao.AcupointDao
import com.dailyread.app.data.local.database.entities.Acupoint
import com.dailyread.app.domain.usecase.AutoSyncManager
import dagger.Lazy
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AcupointRepository @Inject constructor(
    private val acupointDao: AcupointDao,
    private val autoSyncManagerLazy: Lazy<AutoSyncManager>
) {
    fun getAllAcupoints(): Flow<List<Acupoint>> = acupointDao.getAllAcupoints()
    
    suspend fun getAllAcupointsOnce(): List<Acupoint> = acupointDao.getAllAcupoints().first()

    suspend fun getAcupointById(id: Long): Acupoint? = acupointDao.getAcupointById(id)

    suspend fun insert(acupoint: Acupoint): Long {
        val id = acupointDao.insert(acupoint)
        autoSyncManagerLazy.get().triggerAutoSync()
        return id
    }

    suspend fun update(acupoint: Acupoint) {
        acupointDao.update(acupoint)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun delete(acupoint: Acupoint) {
        acupointDao.delete(acupoint)
        autoSyncManagerLazy.get().triggerAutoSync()
    }

    suspend fun searchByAcupoint(query: String): List<Acupoint> = 
        acupointDao.searchByAcupoint(query)

    suspend fun filterByMeridian(meridian: String): List<Acupoint> = 
        acupointDao.filterByMeridian(meridian)

    suspend fun getDistinctMeridians(): List<String> = acupointDao.getDistinctMeridians()

    suspend fun getRandomAcupoint(): Acupoint? = acupointDao.getRandomAcupoint()
    
    suspend fun deleteAcupoints(acupoints: List<Acupoint>) {
        acupointDao.deleteAcupoints(acupoints)
        autoSyncManagerLazy.get().triggerAutoSync()
    }
}
