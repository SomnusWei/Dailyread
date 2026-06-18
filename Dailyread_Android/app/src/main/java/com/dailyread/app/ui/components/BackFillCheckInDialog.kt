package com.dailyread.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Cancel
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import java.time.LocalDate
import java.time.YearMonth
import java.time.format.DateTimeFormatter
import java.time.format.TextStyle
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BackFillCheckInDialog(
    articleId: Long,
    articleTitle: String,
    existingCheckInDates: Set<String>,
    onDismiss: () -> Unit,
    onBackFill: (List<String>) -> Unit,
    onCancelCheckIn: (List<String>) -> Unit
) {
    var selectedDates by remember { mutableStateOf<Set<String>>(emptySet()) }

    val today = LocalDate.now()
    val threeMonthsAgo = today.minusMonths(3)

    // 生成3个月内的所有月份
    val months = remember {
        val start = YearMonth.from(threeMonthsAgo)
        val end = YearMonth.from(today)
        val result = mutableListOf<YearMonth>()
        var current = start
        while (current <= end) {
            result.add(current)
            current = current.plusMonths(1)
        }
        result
    }

    val selectedMonth = remember(selectedDates) {
        selectedDates.firstOrNull()?.let {
            val date = LocalDate.parse(it)
            YearMonth.from(date)
        } ?: YearMonth.from(today)
    }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Column {
                Text("补打卡", style = MaterialTheme.typography.titleLarge)
                Text(articleTitle, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
        },
        text = {
            Column {
                LazyRow(
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(months) { month ->
                        FilterChip(
                            selected = month == selectedMonth,
                            onClick = {
                                // 如果切换月份，清空选中的日期
                                selectedDates = emptySet()
                            },
                            label = {
                                Text(
                                    "${month.year}年${month.month.value}月",
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        )
                    }
                }

                Spacer(modifier = Modifier.height(16.dp))

                MonthCalendar(
                    month = selectedMonth,
                    threeMonthsAgo = threeMonthsAgo,
                    today = today,
                    existingCheckInDates = existingCheckInDates,
                    selectedDates = selectedDates,
                    onDateClick = { date ->
                        selectedDates = if (selectedDates.contains(date)) {
                            selectedDates - date
                        } else {
                            selectedDates + date
                        }
                    }
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    val datesToBackFill = (selectedDates - existingCheckInDates).toList()
                    val datesToCancel = (selectedDates intersect existingCheckInDates).toList()

                    if (datesToBackFill.isNotEmpty()) {
                        onBackFill(datesToBackFill)
                    }
                    if (datesToCancel.isNotEmpty()) {
                        onCancelCheckIn(datesToCancel)
                    }
                    onDismiss()
                }
            ) {
                Text("确认")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

@Composable
fun MonthCalendar(
    month: YearMonth,
    threeMonthsAgo: LocalDate,
    today: LocalDate,
    existingCheckInDates: Set<String>,
    selectedDates: Set<String>,
    onDateClick: (String) -> Unit
) {
    val firstDay = month.atDay(1)
    val daysInMonth = month.lengthOfMonth()
    val dayOfWeek = firstDay.dayOfWeek.value

    Column {
        // 星期标题
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceAround
        ) {
            listOf("一", "二", "三", "四", "五", "六", "日").forEach { day ->
                Text(
                    day,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(4.dp)
                )
            }
        }

        // 日历网格
        Column(
            verticalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            var dayIndex = 1
            while (dayIndex <= daysInMonth) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceAround
                ) {
                    // 填充第一周的空白
                    if (dayIndex == 1) {
                        repeat(dayOfWeek - 1) {
                            Box(modifier = Modifier.size(36.dp))
                        }
                    }

                    // 填充日期
                    val startCol = if (dayIndex == 1) dayOfWeek else 1
                    for (col in startCol..7) {
                        if (dayIndex > daysInMonth) break
                        
                        val date = month.atDay(dayIndex)
                        val dateStr = date.toString()
                        val isWithinRange = date >= threeMonthsAgo && date <= today
                        val isCheckedIn = existingCheckInDates.contains(dateStr)
                        val isSelected = selectedDates.contains(dateStr)

                        DayCell(
                            day = dayIndex,
                            isWithinRange = isWithinRange,
                            isCheckedIn = isCheckedIn,
                            isSelected = isSelected,
                            onClick = { onDateClick(dateStr) }
                        )
                        dayIndex++
                    }
                }
            }
        }
    }
}

@Composable
fun DayCell(
    day: Int,
    isWithinRange: Boolean,
    isCheckedIn: Boolean,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val backgroundColor = when {
        isSelected -> MaterialTheme.colorScheme.primaryContainer
        isCheckedIn -> MaterialTheme.colorScheme.secondaryContainer
        else -> Color.Transparent
    }

    val textColor = when {
        isSelected -> MaterialTheme.colorScheme.onPrimaryContainer
        isCheckedIn -> MaterialTheme.colorScheme.onSecondaryContainer
        !isWithinRange -> MaterialTheme.colorScheme.onSurface.copy(alpha = 0.3f)
        else -> MaterialTheme.colorScheme.onSurface
    }

    Box(
        modifier = Modifier
            .size(36.dp)
            .background(
                color = backgroundColor,
                shape = RoundedCornerShape(8.dp)
            )
            .clickable(enabled = isWithinRange) { onClick() },
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Text(
                day.toString(),
                style = MaterialTheme.typography.bodyMedium,
                color = textColor
            )
            if (isCheckedIn) {
                Spacer(modifier = Modifier.width(2.dp))
                Icon(
                    Icons.Default.Check,
                    contentDescription = null,
                    tint = textColor,
                    modifier = Modifier.size(12.dp)
                )
            }
        }
    }
}
