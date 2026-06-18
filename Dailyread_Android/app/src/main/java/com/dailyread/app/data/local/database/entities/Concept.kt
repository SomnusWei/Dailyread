package com.dailyread.app.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "concepts")
data class Concept(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val subject: String = "",
    val category: String = "",
    val subChapter: String = "",
    val title: String = "",
    val content: String = "",
    val imagePath: String? = null,
    val imageBase64: String? = null,
    val note: String = "",
    val isEnabled: Boolean = true,
    val createTime: String = "",
    val lastModified: String = ""
)
