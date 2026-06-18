package com.dailyread.app.domain.model

data class Article(
    val id: Long = 0,
    val title: String,
    val content: String,
    val contentHtml: String? = null,
    val chineseChars: Int,
    val fontFamily: String = "default",
    val fontSize: Int = 16,
    val fontColor: String = "#000000",
    val isBold: Boolean = false,
    val isReading: Boolean = true,
    val isRequired: Boolean = false,
    val requiredDays: String = "",
    val useIndependentCheckRate: Boolean = false,
    val independentCheckRate: Float = 30.0f,
    val createTime: String
)
