package com.karandaev.roadCrackDetector.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.foundation.isSystemInDarkTheme

private val LightColors = lightColorScheme()
private val DarkColors = darkColorScheme()

@Composable
fun AppTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme() // термин: берём тёмная ли тема в системе
    val scheme = if (dark) DarkColors else LightColors

    MaterialTheme(
        colorScheme = scheme, // термин: явная цветовая схема
        content = content
    )
}