package com.dailyread.app

import android.os.Bundle
import android.view.WindowManager
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.windowsizeclass.ExperimentalMaterial3WindowSizeClassApi
import androidx.compose.material3.windowsizeclass.calculateWindowSizeClass
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.rememberNavController
import com.dailyread.app.data.repository.ConfigRepository
import com.dailyread.app.ui.navigation.AppNavigation
import com.dailyread.app.ui.theme.DailyReadTheme
import com.dailyread.app.ui.utils.rememberAdaptiveLayoutConfig
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3WindowSizeClassApi::class)
@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    @Inject
    lateinit var configRepository: ConfigRepository
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            DailyReadTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    val windowSizeClass = calculateWindowSizeClass(activity = this)
                    val layoutConfig = rememberAdaptiveLayoutConfig(windowSizeClass)
                    val navController = rememberNavController()
                    
                    LaunchedEffect(Unit) {
                        try {
                            configRepository.getConfig().collect { config ->
                                config?.let {
                                    if (it.keepScreenOn) {
                                        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                                    } else {
                                        window.clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)
                                    }
                                }
                            }
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }
                    
                    AppNavigation(
                        navController = navController,
                        layoutConfig = layoutConfig
                    )
                }
            }
        }
    }
}
