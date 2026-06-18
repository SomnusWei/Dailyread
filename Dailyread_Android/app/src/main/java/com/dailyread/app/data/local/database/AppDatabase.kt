package com.dailyread.app.data.local.database
import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.migration.Migration
import androidx.sqlite.db.SupportSQLiteDatabase
import com.dailyread.app.data.local.database.dao.ContentCheckInDao
import com.dailyread.app.data.local.database.dao.ContentDao
import com.dailyread.app.data.local.database.dao.ConfigDao
import com.dailyread.app.data.local.database.dao.ConceptDao
import com.dailyread.app.data.local.database.entities.Content
import com.dailyread.app.data.local.database.entities.ContentCheckIn
import com.dailyread.app.data.local.database.entities.Config
import com.dailyread.app.data.local.database.entities.Concept

val MIGRATION_1_2 = object : Migration(1, 2) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE contents ADD COLUMN isRequired INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE contents ADD COLUMN requiredDays TEXT NOT NULL DEFAULT ''")
    }
}

val MIGRATION_2_3 = object : Migration(2, 3) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE config ADD COLUMN keepScreenOn INTEGER NOT NULL DEFAULT 0")
    }
}

val MIGRATION_3_4 = object : Migration(3, 4) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE contents ADD COLUMN useIndependentCheckRate INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE contents ADD COLUMN independentCheckRate REAL NOT NULL DEFAULT 30.0")
    }
}

val MIGRATION_4_5 = object : Migration(4, 5) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE config ADD COLUMN webdavEnabled INTEGER NOT NULL DEFAULT 0")
        db.execSQL("ALTER TABLE config ADD COLUMN webdavServerUrl TEXT NOT NULL DEFAULT ''")
        db.execSQL("ALTER TABLE config ADD COLUMN webdavUsername TEXT NOT NULL DEFAULT ''")
        db.execSQL("ALTER TABLE config ADD COLUMN webdavPassword TEXT NOT NULL DEFAULT ''")
        db.execSQL("ALTER TABLE config ADD COLUMN webdavRemotePath TEXT NOT NULL DEFAULT '/DailyRead'")
        db.execSQL("ALTER TABLE config ADD COLUMN lastSyncTime TEXT")
    }
}

val MIGRATION_5_6 = object : Migration(5, 6) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE config ADD COLUMN autoSyncWebDav INTEGER NOT NULL DEFAULT 0")
    }
}

val MIGRATION_6_7 = object : Migration(6, 7) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE config ADD COLUMN yesterdayLongArticleIds TEXT NOT NULL DEFAULT ''")
    }
}

val MIGRATION_7_8 = object : Migration(7, 8) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("""
            CREATE TABLE IF NOT EXISTS concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                subject TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                subChapter TEXT NOT NULL DEFAULT '',
                title TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                imagePath TEXT,
                imageBase64 TEXT,
                note TEXT NOT NULL DEFAULT '',
                isEnabled INTEGER NOT NULL DEFAULT 1,
                createTime TEXT NOT NULL DEFAULT '',
                lastModified TEXT NOT NULL DEFAULT ''
            )
        """.trimIndent())
    }
}

val MIGRATION_8_9 = object : Migration(8, 9) {
    override fun migrate(db: SupportSQLiteDatabase) {
        db.execSQL("ALTER TABLE config ADD COLUMN syncArticlesEnabled INTEGER NOT NULL DEFAULT 1")
        db.execSQL("ALTER TABLE config ADD COLUMN syncAcupointsEnabled INTEGER NOT NULL DEFAULT 1")
        db.execSQL("ALTER TABLE config ADD COLUMN syncConceptsEnabled INTEGER NOT NULL DEFAULT 1")
    }
}

@Database(
    entities = [Content::class, ContentCheckIn::class, Config::class, Concept::class],
    version = 9,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun contentDao(): ContentDao
    abstract fun contentCheckInDao(): ContentCheckInDao
    abstract fun configDao(): ConfigDao
    abstract fun conceptDao(): ConceptDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "daily_read_database"
                )
                    .addMigrations(MIGRATION_1_2, MIGRATION_2_3, MIGRATION_3_4, MIGRATION_4_5, MIGRATION_5_6, MIGRATION_6_7, MIGRATION_7_8, MIGRATION_8_9)
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
