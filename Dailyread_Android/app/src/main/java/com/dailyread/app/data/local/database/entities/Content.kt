package com.dailyread.app.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDateTime

@Entity(tableName = "contents")
data class Content(
    @PrimaryKey(autoGenerate = true)
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
    val createTime: String = LocalDateTime.now().toString()
)

fun Content.toDomainModel(): com.dailyread.app.domain.model.Article {
    return com.dailyread.app.domain.model.Article(
        id = id,
        title = title,
        content = content,
        contentHtml = contentHtml,
        chineseChars = chineseChars,
        fontFamily = fontFamily,
        fontSize = fontSize,
        fontColor = fontColor,
        isBold = isBold,
        isReading = isReading,
        isRequired = isRequired,
        requiredDays = requiredDays,
        useIndependentCheckRate = useIndependentCheckRate,
        independentCheckRate = independentCheckRate,
        createTime = createTime
    )
}

fun com.dailyread.app.domain.model.Article.toEntity(): Content {
    return Content(
        id = id,
        title = title,
        content = content,
        contentHtml = contentHtml,
        chineseChars = chineseChars,
        fontFamily = fontFamily,
        fontSize = fontSize,
        fontColor = fontColor,
        isBold = isBold,
        isReading = isReading,
        isRequired = isRequired,
        requiredDays = requiredDays,
        useIndependentCheckRate = useIndependentCheckRate,
        independentCheckRate = independentCheckRate,
        createTime = createTime
    )
}
