package com.dailyread.app.ui.screens.articles

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.dailyread.app.utils.StringUtils
import java.time.LocalDateTime

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddArticleScreen(
    articleId: Long?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: AddArticleViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()

    LaunchedEffect(articleId) {
        if (articleId != null) {
            viewModel.loadArticle(articleId)
        }
    }

    var title by remember { mutableStateOf(uiState.title) }
    var content by remember { mutableStateOf(uiState.content) }
    var isReading by remember { mutableStateOf(uiState.isReading) }
    var isRequired by remember { mutableStateOf(uiState.isRequired) }
    var selectedDays by remember { mutableStateOf(uiState.requiredDays.split(",").filter { it.isNotEmpty() }.toSet()) }

    LaunchedEffect(uiState) {
        title = uiState.title
        content = uiState.content
        isReading = uiState.isReading
        isRequired = uiState.isRequired
        selectedDays = uiState.requiredDays.split(",").filter { it.isNotEmpty() }.toSet()
    }

    val dayLabels = listOf("一", "二", "三", "四", "五", "六", "日")

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (articleId == null) "添加文章" else "编辑文章") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        },
        modifier = modifier
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            OutlinedTextField(
                value = title,
                onValueChange = { title = it },
                label = { Text("标题") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            Spacer(modifier = Modifier.height(16.dp))

            OutlinedTextField(
                value = content,
                onValueChange = { content = it },
                label = { Text("内容") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(500.dp),
                minLines = 5,
                maxLines = 1000
            )

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("加入阅读计划", modifier = Modifier.weight(1f))
                Switch(
                    checked = isReading,
                    onCheckedChange = { isReading = it }
                )
            }

            Spacer(modifier = Modifier.height(16.dp))

            HorizontalDivider()

            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        "必读",
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "必读文章在指定日期必定出现在今日阅读任务，字数不计入任务统计",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
                Switch(
                    checked = isRequired,
                    onCheckedChange = { enabled ->
                        isRequired = enabled
                        if (enabled) {
                            selectedDays = setOf("1", "2", "3", "4", "5", "6", "7")
                        } else {
                            selectedDays = emptySet()
                        }
                    }
                )
            }

            if (isRequired) {
                Spacer(modifier = Modifier.height(16.dp))
                
                Text(
                    "选择必读日期：",
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = FontWeight.Medium
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    dayLabels.forEachIndexed { index, day ->
                        val dayNumber = (index + 1).toString()
                        FilterChip(
                            selected = selectedDays.contains(dayNumber),
                            onClick = {
                                selectedDays = if (selectedDays.contains(dayNumber)) {
                                    selectedDays - dayNumber
                                } else {
                                    selectedDays + dayNumber
                                }
                            },
                            label = { Text(day) }
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Button(
                onClick = {
                    val chineseChars = StringUtils.countChineseChars(content)
                    val requiredDaysStr = if (isRequired) selectedDays.sorted().joinToString(",") else ""
                    viewModel.saveArticle(
                        title = title,
                        content = content,
                        chineseChars = chineseChars,
                        isReading = isReading,
                        isRequired = isRequired,
                        requiredDays = requiredDaysStr
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = title.isNotBlank() && content.isNotBlank()
            ) {
                Text("保存")
            }

            LaunchedEffect(uiState.navigateBack) {
                if (uiState.navigateBack) {
                    android.widget.Toast.makeText(
                        context,
                        if (articleId == null) "添加成功" else "保存成功",
                        android.widget.Toast.LENGTH_SHORT
                    ).show()
                    onBack()
                }
            }
        }
    }
}
