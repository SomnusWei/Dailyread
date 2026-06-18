package com.dailyread.app.data.local.database.dao
import androidx.room.*
import com.dailyread.app.data.local.database.entities.Config
import kotlinx.coroutines.flow.Flow

@Dao
interface ConfigDao {
    @Query("SELECT * FROM config WHERE id = 1")
    fun getConfig(): Flow<Config?>

    @Query("SELECT * FROM config WHERE id = 1")
    suspend fun getConfigOnce(): Config?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertConfig(config: Config)

    @Update
    suspend fun updateConfig(config: Config)
}