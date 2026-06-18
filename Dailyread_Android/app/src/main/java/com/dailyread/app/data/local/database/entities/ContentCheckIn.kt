package com.dailyread.app.data.local.database.entities
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "content_checkin",
    indices = [Index(value = ["contentId", "date"], unique = true)]
)
data class ContentCheckIn(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val contentId: Long,
    val date: String
)
