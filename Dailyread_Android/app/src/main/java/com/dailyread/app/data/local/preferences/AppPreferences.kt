package com.dailyread.app.data.local.preferences
import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "app_preferences")

class AppPreferences(private val context: Context) {
    companion object {
        private val KEY_DAILY_MINUTES = intPreferencesKey("daily_minutes")
        private val KEY_THEME = stringPreferencesKey("theme")
        private val KEY_TARGET_CHECK_RATE = floatPreferencesKey("target_check_rate")
    }

    val dailyMinutes: Flow<Int> = context.dataStore.data.map { preferences ->
        preferences[KEY_DAILY_MINUTES] ?: 20
    }

    val theme: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[KEY_THEME] ?: "system"
    }

    val targetCheckRate: Flow<Float> = context.dataStore.data.map { preferences ->
        preferences[KEY_TARGET_CHECK_RATE] ?: 40.0f
    }

    suspend fun setDailyMinutes(minutes: Int) {
        context.dataStore.edit { preferences ->
            preferences[KEY_DAILY_MINUTES] = minutes
        }
    }

    suspend fun setTheme(theme: String) {
        context.dataStore.edit { preferences ->
            preferences[KEY_THEME] = theme
        }
    }

    suspend fun setTargetCheckRate(rate: Float) {
        context.dataStore.edit { preferences ->
            preferences[KEY_TARGET_CHECK_RATE] = rate
        }
    }
}