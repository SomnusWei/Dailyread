package com.dailyread.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import java.time.LocalDate
import java.time.format.DateTimeFormatter

@Composable
fun Heatmap(
    year: Int,
    checkInData: Map<String, Int>,
    modifier: Modifier = Modifier
) {
    val weeks = remember { 
        try {
            generateWeeks(year)
        } catch (e: Exception) {
            e.printStackTrace()
            emptyList()
        }
    }
    val maxCount = try {
        checkInData.values.maxOrNull() ?: 1
    } catch (e: Exception) {
        e.printStackTrace()
        1
    }

    Column(modifier = modifier) {
        if (weeks.isNotEmpty()) {
            LazyRow(
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                items(weeks.size) { weekIndex ->
                    Column(
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        weeks[weekIndex].days.forEach { day ->
                            val dateStr = try {
                                day.format(DateTimeFormatter.ISO_LOCAL_DATE)
                            } catch (e: Exception) {
                                ""
                            }
                            val count = checkInData[dateStr] ?: 0
                            val color = try {
                                getHeatmapColor(count, maxCount)
                            } catch (e: Exception) {
                                Color(0xFFEBEDF0)
                            }

                            Box(
                                modifier = Modifier
                                    .size(12.dp)
                                    .clip(RoundedCornerShape(2.dp))
                                    .background(color)
                            )
                        }
                    }
                }
            }
        } else {
            Text(
                "暂无数据",
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.padding(16.dp)
            )
        }

        Spacer(modifier = Modifier.height(16.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("少", style = MaterialTheme.typography.bodySmall)
            Spacer(modifier = Modifier.width(8.dp))
            (0..4).forEach { level ->
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(getHeatmapColor(level, 4))
                )
                Spacer(modifier = Modifier.width(4.dp))
            }
            Text("多", style = MaterialTheme.typography.bodySmall)
        }
    }
}

private fun getHeatmapColor(count: Int, maxCount: Int): Color {
    val level = if (maxCount == 0) 0 else (count * 4 / maxCount).coerceIn(0, 4)
    return when (level) {
        0 -> Color(0xFFEBEDF0)
        1 -> Color(0xFF9BE9A8)
        2 -> Color(0xFF40C463)
        3 -> Color(0xFF30A14E)
        4 -> Color(0xFF216E39)
        else -> Color(0xFF216E39)
    }
}

private data class Week(val days: List<LocalDate>)

private fun generateWeeks(year: Int): List<Week> {
    return try {
        val firstDay = LocalDate.of(year, 1, 1)
        val lastDay = LocalDate.of(year, 12, 31)

        val startDay = firstDay.minusDays(firstDay.dayOfWeek.value.toLong() - 1)

        val weeks = mutableListOf<Week>()
        var currentDay = startDay

        while (currentDay <= lastDay) {
            val days = (0..6).map { currentDay.plusDays(it.toLong()) }
            weeks.add(Week(days))
            currentDay = currentDay.plusWeeks(1)
        }

        weeks
    } catch (e: Exception) {
        e.printStackTrace()
        emptyList()
    }
}
