package com.dailyread.app.data.local.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.dailyread.app.data.local.database.dao.AcupointDao
import com.dailyread.app.data.local.database.entities.Acupoint

@Database(
    entities = [Acupoint::class],
    version = 1,
    exportSchema = false
)
abstract class AcupointDatabase : RoomDatabase() {
    abstract fun acupointDao(): AcupointDao

    companion object {
        @Volatile
        private var INSTANCE: AcupointDatabase? = null

        fun getDatabase(context: Context): AcupointDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AcupointDatabase::class.java,
                    "acupoint_database"
                ).build()
                INSTANCE = instance
                instance
            }
        }
    }
}
