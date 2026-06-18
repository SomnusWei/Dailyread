package com.dailyread.app.ui.screens.articles

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.EditCalendar
import androidx.compose.material.icons.filled.Star
import androidx.compose.material.icons.filled.SelectAll
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.Checkbox
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.dailyread.app.ui.components.BackFillCheckInDialog
import com.dailyread.app.ui.components.BottomNavigationBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ArticlesScreen(
    onNavigateToAddArticle: () -> Unit,
    onNavigateToEditArticle: (Long) -> Unit,
    onNavigateToReader: (Long) -> Unit,
    onNavigateToBottomNav: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ArticlesViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    var showBackFillDialogForArticle by remember { mutableStateOf<Long?>(null) }
    var articleToDelete by remember { mutableStateOf<ArticleWithCheckRate?>(null) }
    var showRequiredDialogForArticle by remember { mutableStateOf<ArticleWithCheckRate?>(null) }
    var showIndependentRateDialogForArticle by remember { mutableStateOf<Long?>(null) }
    var showDeleteSelectedDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.loadArticles()
    }

    Scaffold(
        topBar = {
            if (uiState.isSelectionMode) {
                TopAppBar(
                    title = { Text("已选择 ${uiState.selectedArticleIds.size} 篇") },
                    navigationIcon = {
                        IconButton(onClick = { viewModel.clearSelection() }) {
                            Icon(Icons.Default.Close, contentDescription = "取消选择")
                        }
                    },
                    actions = {
                        if (uiState.selectedArticleIds.isNotEmpty()) {
                            IconButton(onClick = { viewModel.selectAllArticles() }) {
                                Icon(Icons.Default.SelectAll, contentDescription = "全选")
                            }
                            IconButton(onClick = { showDeleteSelectedDialog = true }) {
                                Icon(Icons.Default.Delete, contentDescription = "批量删除")
                            }
                        }
                    }
                )
            } else {
                TopAppBar(
                    title = { Text("文章管理") },
                    actions = {
                        IconButton(onClick = onNavigateToAddArticle) {
                            Icon(Icons.Default.Add, contentDescription = "添加文章")
                        }
                    }
                )
            }
        },
        bottomBar = {
            BottomNavigationBar(
                currentRoute = "articles",
                onNavigate = { route ->
                    if (route == "articles") {
                        // Already on articles screen
                    } else {
                        onNavigateToBottomNav(route)
                    }
                }
            )
        },
        modifier = modifier
    ) { paddingValues ->
        if (uiState.articles.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        "暂无文章，请添加",
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(onClick = onNavigateToAddArticle) {
                        Icon(Icons.Default.Add, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("添加文章")
                    }
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp)
            ) {
                items(uiState.articles) { articleWithRate ->
                    ArticleListItem(
                        articleWithRate = articleWithRate,
                        isSelected = uiState.selectedArticleIds.contains(articleWithRate.article.id),
                        isSelectionMode = uiState.isSelectionMode,
                        onToggleSelection = { viewModel.toggleArticleSelection(articleWithRate.article.id) },
                        onEdit = { onNavigateToEditArticle(articleWithRate.article.id) },
                        onDelete = { articleToDelete = articleWithRate },
                        onRead = { onNavigateToReader(articleWithRate.article.id) },
                        onToggleReading = { viewModel.toggleReading(articleWithRate.article) },
                        onToggleRequired = { showRequiredDialogForArticle = articleWithRate },
                        onBackFill = { showBackFillDialogForArticle = articleWithRate.article.id },
                        onToggleIndependentRate = { showIndependentRateDialogForArticle = articleWithRate.article.id }
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                }
            }
        }

        showBackFillDialogForArticle?.let { articleId ->
            val articleWithRate = uiState.articles.find { it.article.id == articleId }
            articleWithRate?.let {
                BackFillCheckInDialog(
                    articleId = articleId,
                    articleTitle = articleWithRate.article.title,
                    existingCheckInDates = articleWithRate.checkInDates,
                    onDismiss = { showBackFillDialogForArticle = null },
                    onBackFill = { dates ->
                        viewModel.backFillCheckIn(articleId, dates)
                    },
                    onCancelCheckIn = { dates ->
                        viewModel.cancelCheckIn(articleId, dates)
                    }
                )
            }
        }

        articleToDelete?.let { article ->
            AlertDialog(
                onDismissRequest = { articleToDelete = null },
                title = { Text("确认删除") },
                text = { Text("确定要删除文章'${article.article.title}'吗？此操作无法撤销。") },
                confirmButton = {
                    TextButton(
                        onClick = {
                            viewModel.deleteArticle(article.article)
                            articleToDelete = null
                        },
                        colors = ButtonDefaults.textButtonColors(
                            contentColor = MaterialTheme.colorScheme.error
                        )
                    ) {
                        Text("删除")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { articleToDelete = null }) {
                        Text("取消")
                    }
                }
            )
        }

        showRequiredDialogForArticle?.let { articleWithRate ->
            RequiredDaysDialog(
                articleTitle = articleWithRate.article.title,
                isRequired = articleWithRate.article.isRequired,
                selectedDays = articleWithRate.article.requiredDays.split(",").filter { it.isNotEmpty() }.toSet(),
                onDismiss = { showRequiredDialogForArticle = null },
                onToggleRequired = { enabled ->
                    viewModel.toggleRequired(articleWithRate.article)
                    if (!enabled) {
                        showRequiredDialogForArticle = null
                    }
                },
                onUpdateDays = { days ->
                    viewModel.updateRequiredDays(articleWithRate.article, days)
                }
            )
        }

        showIndependentRateDialogForArticle?.let { articleId ->
            val articleWithRate = uiState.articles.find { it.article.id == articleId }
            articleWithRate?.let {
                IndependentCheckRateDialog(
                    articleTitle = articleWithRate.article.title,
                    useIndependentRate = articleWithRate.article.useIndependentCheckRate,
                    independentRate = articleWithRate.article.independentCheckRate,
                    onDismiss = { showIndependentRateDialogForArticle = null },
                    onConfirm = { enabled, rate ->
                        viewModel.updateIndependentCheckRateWithEnabled(
                            articleWithRate.article,
                            enabled,
                            rate
                        )
                    }
                )
            }
        }

        if (showDeleteSelectedDialog) {
            AlertDialog(
                onDismissRequest = { showDeleteSelectedDialog = false },
                title = { Text("确认批量删除") },
                text = { Text("确定要删除已选择的 ${uiState.selectedArticleIds.size} 篇文章吗？此操作无法撤销。") },
                confirmButton = {
                    TextButton(
                        onClick = {
                            viewModel.deleteSelectedArticles()
                            showDeleteSelectedDialog = false
                        },
                        colors = ButtonDefaults.textButtonColors(
                            contentColor = MaterialTheme.colorScheme.error
                        )
                    ) {
                        Text("删除")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showDeleteSelectedDialog = false }) {
                        Text("取消")
                    }
                }
            )
        }
    }
}

@Composable
fun RequiredDaysDialog(
    articleTitle: String,
    isRequired: Boolean,
    selectedDays: Set<String>,
    onDismiss: () -> Unit,
    onToggleRequired: (Boolean) -> Unit,
    onUpdateDays: (String) -> Unit
) {
    var localSelectedDays by remember { mutableStateOf(selectedDays) }
    var localIsRequired by remember { mutableStateOf(isRequired) }
    val dayLabels = listOf("一", "二", "三", "四", "五", "六", "日")

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("设置必读") },
        text = {
            Column {
                Text(
                    "文章：$articleTitle",
                    style = MaterialTheme.typography.bodyMedium
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("启用必读")
                    Switch(
                        checked = localIsRequired,
                        onCheckedChange = { enabled ->
                            localIsRequired = enabled
                            onToggleRequired(enabled)
                            if (enabled) {
                                localSelectedDays = setOf("1", "2", "3", "4", "5", "6", "7")
                            } else {
                                localSelectedDays = emptySet()
                            }
                        }
                    )
                }
                
                if (localIsRequired) {
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text(
                        "选择必读日期：",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        dayLabels.forEachIndexed { index, day ->
                            val dayNumber = (index + 1).toString()
                            FilterChip(
                                selected = localSelectedDays.contains(dayNumber),
                                onClick = {
                                    localSelectedDays = if (localSelectedDays.contains(dayNumber)) {
                                        localSelectedDays - dayNumber
                                    } else {
                                        localSelectedDays + dayNumber
                                    }
                                },
                                label = { Text(day) }
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (localIsRequired && localSelectedDays.isNotEmpty()) {
                        onUpdateDays(localSelectedDays.sorted().joinToString(","))
                    } else if (!localIsRequired) {
                        onUpdateDays("")
                    }
                    onDismiss()
                }
            ) {
                Text("确定")
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
fun IndependentCheckRateDialog(
    articleTitle: String,
    useIndependentRate: Boolean,
    independentRate: Float,
    onDismiss: () -> Unit,
    onConfirm: (Boolean, Float) -> Unit
) {
    var localUseIndependentRate by remember { mutableStateOf(useIndependentRate) }
    var localIndependentRate by remember { mutableStateOf(independentRate) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("独立完成率设置") },
        text = {
            Column {
                Text(
                    "文章：$articleTitle",
                    style = MaterialTheme.typography.bodyMedium
                )
                
                Spacer(modifier = Modifier.height(16.dp))
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text("启用独立完成率")
                    Switch(
                        checked = localUseIndependentRate,
                        onCheckedChange = { enabled ->
                            localUseIndependentRate = enabled
                            if (!enabled) {
                                localIndependentRate = 30f
                            }
                        }
                    )
                }
                
                if (localUseIndependentRate) {
                    Spacer(modifier = Modifier.height(16.dp))
                    
                    Text(
                        "独立目标完成率：${localIndependentRate.toInt()}%",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    
                    Spacer(modifier = Modifier.height(8.dp))
                    
                    Slider(
                        value = localIndependentRate,
                        onValueChange = { newRate ->
                            localIndependentRate = newRate
                        },
                        valueRange = 5f..100f,
                        steps = 18
                    )
                }
            }
        },
        confirmButton = {
            TextButton(onClick = {
                onConfirm(localUseIndependentRate, localIndependentRate)
                onDismiss()
            }) {
                Text("确定")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun ArticleListItem(
    articleWithRate: ArticleWithCheckRate,
    isSelected: Boolean,
    isSelectionMode: Boolean,
    onToggleSelection: () -> Unit,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
    onRead: () -> Unit,
    onToggleReading: () -> Unit,
    onToggleRequired: () -> Unit,
    onBackFill: () -> Unit,
    onToggleIndependentRate: () -> Unit,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .combinedClickable(
                onLongClick = {
                    if (!isSelectionMode) {
                        onToggleSelection()
                    }
                },
                onClick = {
                    if (isSelectionMode) {
                        onToggleSelection()
                    }
                }
            ),
        shape = RoundedCornerShape(8.dp),
        colors = if (isSelected) {
            CardDefaults.cardColors(
                containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.5f)
            )
        } else {
            CardDefaults.cardColors()
        }
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                if (isSelectionMode) {
                    Checkbox(
                        checked = isSelected,
                        onCheckedChange = { onToggleSelection() },
                        modifier = Modifier.padding(end = 8.dp)
                    )
                }
                Column(modifier = Modifier.weight(1f)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(
                            articleWithRate.article.title,
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                        if (articleWithRate.article.isRequired) {
                            Spacer(modifier = Modifier.width(4.dp))
                            Text(
                                "（必读）",
                                style = MaterialTheme.typography.labelSmall,
                                color = MaterialTheme.colorScheme.error
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "${articleWithRate.article.chineseChars} 字",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Row(
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "完成率: ${articleWithRate.checkRate.toInt()}%",
                            style = MaterialTheme.typography.bodySmall
                        )
                        if (articleWithRate.article.useIndependentCheckRate) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Card(
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                                ),
                                modifier = Modifier.padding(vertical = 2.dp, horizontal = 6.dp)
                            ) {
                                Text(
                                    "独立目标: ${articleWithRate.article.independentCheckRate.toInt()}%",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer,
                                    modifier = Modifier.padding(vertical = 2.dp, horizontal = 8.dp)
                                )
                            }
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Card(
                            colors = CardDefaults.cardColors(
                                containerColor = when {
                                    articleWithRate.article.isReading && articleWithRate.article.isRequired -> 
                                        MaterialTheme.colorScheme.tertiaryContainer
                                    articleWithRate.article.isReading -> 
                                        MaterialTheme.colorScheme.primary
                                    else -> 
                                        MaterialTheme.colorScheme.surfaceVariant
                                }
                            ),
                            modifier = Modifier.padding(vertical = 2.dp, horizontal = 6.dp)
                        ) {
                            Text(
                                when {
                                    articleWithRate.article.isReading && articleWithRate.article.isRequired -> "阅读中·必读"
                                    articleWithRate.article.isReading -> "阅读中"
                                    articleWithRate.article.isRequired -> "必读"
                                    else -> "已暂停"
                                },
                                style = MaterialTheme.typography.labelSmall,
                                color = when {
                                    articleWithRate.article.isReading -> 
                                        MaterialTheme.colorScheme.onPrimary
                                    else -> 
                                        MaterialTheme.colorScheme.onSurfaceVariant
                                },
                                modifier = Modifier.padding(vertical = 2.dp, horizontal = 8.dp)
                            )
                        }
                    }
                }
                Row {
                    IconButton(onClick = onEdit) {
                        Icon(Icons.Default.Edit, contentDescription = "编辑")
                    }
                    IconButton(onClick = onDelete) {
                        Icon(Icons.Default.Delete, contentDescription = "删除")
                    }
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Button(
                    onClick = onRead,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("阅读")
                }
                OutlinedButton(
                    onClick = onToggleReading,
                    modifier = Modifier.weight(1f)
                ) {
                    Text(
                        if (articleWithRate.article.isReading) "暂停阅读" else "开始阅读"
                    )
                }
                IconButton(
                    onClick = onToggleRequired,
                    modifier = Modifier.size(48.dp),
                    colors = IconButtonDefaults.iconButtonColors(
                        containerColor = if (articleWithRate.article.isRequired) {
                            MaterialTheme.colorScheme.errorContainer
                        } else {
                            MaterialTheme.colorScheme.surfaceVariant
                        },
                        contentColor = if (articleWithRate.article.isRequired) {
                            MaterialTheme.colorScheme.error
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                ) {
                    Icon(
                        Icons.Default.Star,
                        contentDescription = "必读设置",
                        modifier = Modifier.size(24.dp)
                    )
                }
                IconButton(
                    onClick = onToggleIndependentRate,
                    modifier = Modifier.size(48.dp),
                    colors = IconButtonDefaults.iconButtonColors(
                        containerColor = if (articleWithRate.article.useIndependentCheckRate) {
                            MaterialTheme.colorScheme.secondaryContainer
                        } else {
                            MaterialTheme.colorScheme.surfaceVariant
                        },
                        contentColor = if (articleWithRate.article.useIndependentCheckRate) {
                            MaterialTheme.colorScheme.secondary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        }
                    )
                ) {
                    Text(
                        "目标",
                        style = MaterialTheme.typography.labelSmall,
                        fontWeight = FontWeight.Bold
                    )
                }
                IconButton(
                    onClick = onBackFill,
                    modifier = Modifier.size(48.dp),
                    colors = IconButtonDefaults.iconButtonColors(
                        containerColor = MaterialTheme.colorScheme.tertiaryContainer,
                        contentColor = MaterialTheme.colorScheme.onTertiaryContainer
                    )
                ) {
                    Icon(
                        Icons.Default.EditCalendar,
                        contentDescription = "补打卡",
                        modifier = Modifier.size(24.dp)
                    )
                }
            }
        }
    }
}
