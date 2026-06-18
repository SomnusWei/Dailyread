package com.dailyread.app.ui.screens.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.dailyread.app.domain.model.Article
import com.dailyread.app.ui.components.BottomNavigationBar
import com.dailyread.app.ui.components.Heatmap
import com.dailyread.app.ui.utils.AdaptiveLayoutConfig
import java.time.LocalDate

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onNavigateToArticle: (Long) -> Unit,
    onNavigateToAddArticle: () -> Unit,
    onNavigateToBottomNav: (String) -> Unit,
    layoutConfig: AdaptiveLayoutConfig,
    modifier: Modifier = Modifier,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    LaunchedEffect(Unit) {
        viewModel.loadData()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("每日阅读") }
            )
        },
        bottomBar = {
            BottomNavigationBar(
                currentRoute = "home",
                onNavigate = { route ->
                    onNavigateToBottomNav(route)
                }
            )
        },
        modifier = modifier
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues),
            contentPadding = PaddingValues(layoutConfig.contentPadding),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            item {
                Box(modifier = Modifier.widthIn(max = layoutConfig.maxContentWidth)) {
                    Column {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(bottom = 16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                "今日任务",
                                style = MaterialTheme.typography.headlineSmall,
                                fontWeight = FontWeight.Bold,
                                fontSize = MaterialTheme.typography.headlineSmall.fontSize * layoutConfig.fontSizeMultiplier
                            )
                            
                            if (uiState.todayTasks.isNotEmpty()) {
                                Card(
                                    colors = CardDefaults.cardColors(
                                        containerColor = MaterialTheme.colorScheme.primaryContainer
                                    )
                                ) {
                                    Text(
                                        "总字数: ${uiState.totalWords} 字",
                                        style = MaterialTheme.typography.labelMedium,
                                        fontSize = MaterialTheme.typography.labelMedium.fontSize * layoutConfig.fontSizeMultiplier,
                                        color = MaterialTheme.colorScheme.onPrimaryContainer,
                                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp)
                                    )
                                }
                            }
                        }

                        if (uiState.todayTasks.isEmpty()) {
                            Text(
                                "暂无文章，请先添加",
                                style = MaterialTheme.typography.bodyLarge,
                                fontSize = MaterialTheme.typography.bodyLarge.fontSize * layoutConfig.fontSizeMultiplier,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                modifier = Modifier.padding(vertical = 32.dp)
                            )
                        } else {
                            uiState.todayTasks.forEach { article ->
                                ArticleItem(
                                    article = article,
                                    isCheckedIn = uiState.checkedInArticles.contains(article.id),
                                    onClick = { onNavigateToArticle(article.id) },
                                    layoutConfig = layoutConfig
                                )
                                Spacer(modifier = Modifier.height(8.dp))
                            }
                        }

                        Spacer(modifier = Modifier.height(24.dp))
                        Text(
                            "阅读热力图",
                            style = MaterialTheme.typography.headlineSmall,
                            fontWeight = FontWeight.Bold,
                            fontSize = MaterialTheme.typography.headlineSmall.fontSize * layoutConfig.fontSizeMultiplier,
                            modifier = Modifier.padding(bottom = 16.dp)
                        )

                        Heatmap(
                            year = LocalDate.now().year,
                            checkInData = uiState.heatmapData,
                            modifier = Modifier.fillMaxWidth()
                        )

                        Spacer(modifier = Modifier.height(80.dp))
                    }
                }
            }
        }
    }
}

@Composable
fun ArticleItem(
    article: Article,
    isCheckedIn: Boolean,
    onClick: () -> Unit,
    layoutConfig: AdaptiveLayoutConfig,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        colors = CardDefaults.cardColors(
            containerColor = if (isCheckedIn) {
                MaterialTheme.colorScheme.secondaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            }
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(layoutConfig.contentPadding),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        article.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontSize = MaterialTheme.typography.titleMedium.fontSize * layoutConfig.fontSizeMultiplier,
                        fontWeight = FontWeight.Bold
                    )
                    if (article.isRequired) {
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(
                            "（必读）",
                            style = MaterialTheme.typography.labelSmall,
                            fontSize = MaterialTheme.typography.labelSmall.fontSize * layoutConfig.fontSizeMultiplier,
                            color = MaterialTheme.colorScheme.error
                        )
                    }
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "${article.chineseChars} 字",
                    style = MaterialTheme.typography.bodySmall,
                    fontSize = MaterialTheme.typography.bodySmall.fontSize * layoutConfig.fontSizeMultiplier,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (isCheckedIn) {
                Icon(
                    Icons.Default.Check,
                    contentDescription = "已打卡",
                    tint = MaterialTheme.colorScheme.secondary
                )
            }
        }
    }
}
