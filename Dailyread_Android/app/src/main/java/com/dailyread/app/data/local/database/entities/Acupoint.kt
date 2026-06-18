package com.dailyread.app.data.local.database.entities

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "acupoints")
data class Acupoint(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val acupoint: String,
    val meridian: String,
    val acupointProperty: String = "",
    val location: String = "",
    val function: String = "",
    val indications: String = "",
    val anatomy: String = "",
    val operation: String = "",
    val contraindications: String = "",
    val locationImagePath: String? = null,
    val locationImageBase64: String? = null,
    val note: String = "",
    val createTime: String = ""
)
