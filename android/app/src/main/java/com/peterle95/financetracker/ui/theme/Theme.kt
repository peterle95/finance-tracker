package com.peterle95.financetracker.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val LightColors = lightColorScheme(
    primary = Color(0xFF245B4A),
    secondary = Color(0xFF6F4E37),
    tertiary = Color(0xFF4E5C82),
    background = Color(0xFFFAFBF8),
    surface = Color(0xFFFFFFFF),
    error = Color(0xFFB3261E),
)

@Composable
fun FinanceTrackerTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColors,
        typography = MaterialTheme.typography,
        content = content,
    )
}
