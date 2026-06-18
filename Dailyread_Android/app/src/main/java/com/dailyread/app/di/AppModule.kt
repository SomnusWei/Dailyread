package com.dailyread.app.di

import android.content.Context
import com.dailyread.app.data.local.database.AcupointDatabase
import com.dailyread.app.data.local.database.AppDatabase
import com.dailyread.app.data.local.database.dao.AcupointDao
import com.dailyread.app.data.local.database.dao.ContentCheckInDao
import com.dailyread.app.data.local.database.dao.ContentDao
import com.dailyread.app.data.local.database.dao.ConfigDao
import com.dailyread.app.data.local.database.dao.ConceptDao
import com.dailyread.app.data.local.preferences.AppPreferences
import com.dailyread.app.data.repository.AcupointRepository
import com.dailyread.app.data.repository.CheckInRepository
import com.dailyread.app.data.repository.ConfigRepository
import com.dailyread.app.data.repository.ContentRepository
import com.dailyread.app.data.repository.ConceptRepository
import com.dailyread.app.domain.usecase.AutoSyncManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {
    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return AppDatabase.getDatabase(context)
    }

    @Provides
    @Singleton
    fun provideAcupointDatabase(@ApplicationContext context: Context): AcupointDatabase {
        return AcupointDatabase.getDatabase(context)
    }

    @Provides
    @Singleton
    fun provideContentDao(database: AppDatabase): ContentDao {
        return database.contentDao()
    }

    @Provides
    @Singleton
    fun provideContentCheckInDao(database: AppDatabase): ContentCheckInDao {
        return database.contentCheckInDao()
    }

    @Provides
    @Singleton
    fun provideConfigDao(database: AppDatabase): ConfigDao {
        return database.configDao()
    }

    @Provides
    @Singleton
    fun provideAcupointDao(database: AcupointDatabase): AcupointDao {
        return database.acupointDao()
    }

    @Provides
    @Singleton
    fun provideConceptDao(database: AppDatabase): ConceptDao {
        return database.conceptDao()
    }

    @Provides
    @Singleton
    fun provideContentRepository(contentDao: ContentDao): ContentRepository {
        return ContentRepository(contentDao)
    }

    @Provides
    @Singleton
    fun provideCheckInRepository(contentCheckInDao: ContentCheckInDao): CheckInRepository {
        return CheckInRepository(contentCheckInDao)
    }

    @Provides
    @Singleton
    fun provideConfigRepository(configDao: ConfigDao): ConfigRepository {
        return ConfigRepository(configDao)
    }



    @Provides
    @Singleton
    fun provideAppPreferences(@ApplicationContext context: Context): AppPreferences {
        return AppPreferences(context)
    }
}
