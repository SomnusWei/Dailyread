package com.dailyread.app.ui.theme
import androidx.compose.ui.graphics.Color

val LightColors = androidx.compose.material3.lightColorScheme(
    primary = Color(0xFF0078D4),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE6F4FF),
    onPrimaryContainer = Color(0xFF004B8D),
    secondary = Color(0xFF40C463),
    onSecondary = Color.White,
    background = Color.White,
    onBackground = Color(0xFF1A1A1A),
    surface = Color(0xFFF5F7FA),
    onSurface = Color(0xFF1A1A1A),
    error = Color(0xFFD13438),
)

val DarkColors = androidx.compose.material3.darkColorScheme(
    primary = Color(0xFF60CDFF),
    onPrimary = Color(0xFF00325B),
    primaryContainer = Color(0xFF004B8D),
    onPrimaryContainer = Color(0xFFE6F4FF),
    secondary = Color(0xFF9BE9A8),
    onSecondary = Color(0xFF003918),
    background = Color(0xFF1A1A1A),
    onBackground = Color(0xFFE6E6E6),
    surface = Color(0xFF2B2B2C),
    onSurface = Color(0xFFE6E6E6),
    error = Color(0xFFFF8389),
)
