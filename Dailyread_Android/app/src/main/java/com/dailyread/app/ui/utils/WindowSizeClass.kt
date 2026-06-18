package com.dailyread.app.ui.utils

import androidx.compose.material3.windowsizeclass.ExperimentalMaterial3WindowSizeClassApi
import androidx.compose.material3.windowsizeclass.WindowHeightSizeClass
import androidx.compose.material3.windowsizeclass.WindowSizeClass
import androidx.compose.material3.windowsizeclass.WindowWidthSizeClass
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp

enum class DeviceType {
    PHONE,
    FOLDABLE_INNER,
    TABLET
}

data class AdaptiveLayoutConfig(
    val deviceType: DeviceType,
    val contentPadding: Dp,
    val maxContentWidth: Dp,
    val fontSizeMultiplier: Float
)

@OptIn(ExperimentalMaterial3WindowSizeClassApi::class)
@Composable
fun rememberAdaptiveLayoutConfig(
    windowSizeClass: WindowSizeClass? = null
): AdaptiveLayoutConfig {
    val configuration = LocalConfiguration.current
    val screenWidthDp = configuration.screenWidthDp
    val screenHeightDp = configuration.screenHeightDp

    val deviceType = when {
        screenWidthDp >= 840 -> DeviceType.FOLDABLE_INNER
        screenWidthDp >= 600 -> DeviceType.TABLET
        else -> DeviceType.PHONE
    }

    return remember(screenWidthDp, screenHeightDp) {
        when (deviceType) {
            DeviceType.PHONE -> AdaptiveLayoutConfig(
                deviceType = DeviceType.PHONE,
                contentPadding = 16.dp,
                maxContentWidth = 560.dp,
                fontSizeMultiplier = 1.0f
            )
            DeviceType.FOLDABLE_INNER -> AdaptiveLayoutConfig(
                deviceType = DeviceType.FOLDABLE_INNER,
                contentPadding = 32.dp,
                maxContentWidth = 720.dp,
                fontSizeMultiplier = 1.15f
            )
            DeviceType.TABLET -> AdaptiveLayoutConfig(
                deviceType = DeviceType.TABLET,
                contentPadding = 48.dp,
                maxContentWidth = 800.dp,
                fontSizeMultiplier = 1.1f
            )
        }
    }
}
