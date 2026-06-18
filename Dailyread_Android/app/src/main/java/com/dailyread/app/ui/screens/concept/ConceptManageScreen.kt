package com.dailyread.app.ui.screens.concept

import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.dailyread.app.data.local.database.entities.Concept
import com.dailyread.app.ui.components.BottomNavigationBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConceptManageScreen(
    onNavigateToBottomNav: (String) -> Unit,
    onNavigateToAdd: () -> Unit,
    onNavigateToEdit: (Long) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ConceptViewModel = hiltViewModel()
) {
    val uiState by viewModel.manageUiState.collectAsState()
    var showDeleteConfirmDialog by remember { mutableStateOf(false) }
    var showSearchDialog by remember { mutableStateOf(false) }
    var showFilterDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.loadAllConcepts()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(if (uiState.selectedConcepts.isNotEmpty()) {
                        "已选择 ${uiState.selectedConcepts.size} 项"
                    } else {
                        "概念管理"
                    })
                },
                actions = {
                    if (uiState.selectedConcepts.isNotEmpty()) {
                        IconButton(onClick = { showDeleteConfirmDialog = true }) {
                            Icon(Icons.Default.Delete, contentDescription = "删除选中")
                        }
                        IconButton(onClick = { viewModel.selectAll() }) {
                            Icon(Icons.Default.SelectAll, contentDescription = "全选")
                        }
                        IconButton(onClick = { viewModel.clearSelection() }) {
                            Icon(Icons.Default.Close, contentDescription = "取消选择")
                        }
                    } else {
                        IconButton(onClick = { showSearchDialog = true }) {
                            Icon(Icons.Default.Search, contentDescription = "搜索")
                        }
                        IconButton(onClick = { showFilterDialog = true }) {
                            Icon(Icons.Default.FilterList, contentDescription = "筛选")
                        }
                    }
                }
            )
        },
        bottomBar = {
            BottomNavigationBar(
                currentRoute = "concept_manage",
                onNavigate = onNavigateToBottomNav
            )
        },
        floatingActionButton = {
            if (uiState.selectedConcepts.isEmpty()) {
                FloatingActionButton(onClick = onNavigateToAdd) {
                    Icon(Icons.Default.Add, contentDescription = "添加概念")
                }
            }
        },
        modifier = modifier
    ) { paddingValues ->
        if (uiState.isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (uiState.concepts.isEmpty()) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(
                        "暂无概念数据",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "点击右下角按钮添加概念",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(uiState.concepts, key = { it.id }) { concept ->
                    ConceptItem(
                        concept = concept,
                        isSelected = uiState.selectedConcepts.contains(concept.id),
                        isSelectionMode = uiState.selectedConcepts.isNotEmpty(),
                        onSelect = { viewModel.toggleSelectConcept(concept.id) },
                        onClick = { onNavigateToEdit(concept.id) },
                        onLongClick = { viewModel.toggleSelectConcept(concept.id) },
                        onToggleEnabled = { enabled -> viewModel.toggleConceptEnabled(concept.id, enabled) }
                    )
                }
            }
        }
    }

    if (showDeleteConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteConfirmDialog = false },
            title = { Text("确认删除") },
            text = {
                Text("确定要删除选中的 ${uiState.selectedConcepts.size} 个概念吗？")
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.deleteSelected()
                        showDeleteConfirmDialog = false
                    }
                ) {
                    Text("删除", color = MaterialTheme.colorScheme.error)
                }
            },
            dismissButton = {
                TextButton(onClick = { showDeleteConfirmDialog = false }) {
                    Text("取消")
                }
            }
        )
    }

    if (showSearchDialog) {
        var searchQuery by remember { mutableStateOf(uiState.searchQuery) }
        AlertDialog(
            onDismissRequest = { showSearchDialog = false },
            title = { Text("搜索概念") },
            text = {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    label = { Text("概念标题") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.searchConcepts(searchQuery)
                        showSearchDialog = false
                    }
                ) {
                    Text("搜索")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSearchDialog = false }) {
                    Text("取消")
                }
            }
        )
    }

    if (showFilterDialog) {
        var selectedCategory by remember { mutableStateOf(uiState.selectedCategory) }
        var selectedSubject by remember { mutableStateOf(uiState.selectedSubject) }
        var selectedSubChapter by remember { mutableStateOf(uiState.selectedSubChapter) }
        
        // 计算各个分类、科目、子章节的数量
        val allConcepts = remember(uiState.allConcepts) {
            uiState.allConcepts.toList()
        }
        
        // 一级菜单：分类
        val categoryCounts = remember(allConcepts) {
            allConcepts.groupBy { it.category }.mapValues { it.value.size }
        }
        
        val allCategories = remember(allConcepts) {
            allConcepts.map { it.category }.distinct().sorted()
        }
        
        // 根据选中的分类，获取对应的科目
        val filteredSubjects = remember(selectedCategory, allConcepts) {
            if (selectedCategory == null) {
                // 没有选择分类时，显示所有科目（用于显示数量）
                allConcepts.map { it.subject }.distinct().sorted()
            } else {
                allConcepts.filter { it.category == selectedCategory }
                    .map { it.subject }
                    .distinct()
                    .sorted()
            }
        }
        
        val subjectCounts = remember(selectedCategory, allConcepts) {
            if (selectedCategory == null) {
                emptyMap()
            } else {
                allConcepts.filter { it.category == selectedCategory }
                    .groupBy { it.subject }
                    .mapValues { it.value.size }
            }
        }
        
        // 根据选中的分类和科目，获取对应的子章节
        val filteredSubChapters = remember(selectedCategory, selectedSubject, allConcepts) {
            if (selectedCategory == null || selectedSubject == null) {
                emptyList()
            } else {
                allConcepts.filter { it.category == selectedCategory && it.subject == selectedSubject }
                    .map { it.subChapter }
                    .distinct()
                    .sorted()
            }
        }
        
        val subChapterCounts = remember(selectedCategory, selectedSubject, allConcepts) {
            if (selectedCategory == null || selectedSubject == null) {
                emptyMap()
            } else {
                allConcepts.filter { it.category == selectedCategory && it.subject == selectedSubject }
                    .groupBy { it.subChapter }
                    .mapValues { it.value.size }
            }
        }

        AlertDialog(
            onDismissRequest = { showFilterDialog = false },
            title = { Text("分级筛选概念") },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    // 一级菜单：分类
                    Text("第一步：选择分类", style = MaterialTheme.typography.titleMedium)
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedCategory == null,
                            onClick = { 
                                selectedCategory = null 
                                selectedSubject = null
                                selectedSubChapter = null
                            }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("全部", style = MaterialTheme.typography.bodyLarge)
                    }
                    allCategories.forEach { category ->
                        val count = categoryCounts[category] ?: 0
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = selectedCategory == category,
                                onClick = { 
                                    selectedCategory = category 
                                    selectedSubject = null
                                    selectedSubChapter = null
                                }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                if (category.isEmpty()) "未分类" else category, 
                                style = MaterialTheme.typography.bodyLarge
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "($count)",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    
                    // 二级菜单：科目
                    if (selectedCategory != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text("第二步：选择科目", style = MaterialTheme.typography.titleMedium)
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = selectedSubject == null,
                                onClick = { 
                                    selectedSubject = null
                                    selectedSubChapter = null
                                }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("全部", style = MaterialTheme.typography.bodyLarge)
                        }
                        filteredSubjects.forEach { subject ->
                            val count = subjectCounts[subject] ?: 0
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                RadioButton(
                                    selected = selectedSubject == subject,
                                    onClick = { 
                                        selectedSubject = subject
                                        selectedSubChapter = null
                                    }
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    if (subject.isEmpty()) "未分类" else subject, 
                                    style = MaterialTheme.typography.bodyLarge
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    "($count)",
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        
                        // 三级菜单：子章节
                        if (selectedSubject != null) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text("第三步：选择子章节", style = MaterialTheme.typography.titleMedium)
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(vertical = 4.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                RadioButton(
                                    selected = selectedSubChapter == null,
                                    onClick = { selectedSubChapter = null }
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("全部", style = MaterialTheme.typography.bodyLarge)
                            }
                            filteredSubChapters.forEach { subChapter ->
                                val count = subChapterCounts[subChapter] ?: 0
                                Row(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 4.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    RadioButton(
                                        selected = selectedSubChapter == subChapter,
                                        onClick = { selectedSubChapter = subChapter }
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        if (subChapter.isEmpty()) "未分类" else subChapter, 
                                        style = MaterialTheme.typography.bodyLarge
                                    )
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        "($count)",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.applyFilters(
                            selectedCategory,
                            selectedSubject,
                            selectedSubChapter
                        )
                        showFilterDialog = false
                    }
                ) {
                    Text("确定")
                }
            },
            dismissButton = {
                Row {
                    TextButton(onClick = { 
                        viewModel.clearFilters()
                        showFilterDialog = false 
                    }) {
                        Text("清除筛选")
                    }
                    TextButton(onClick = { showFilterDialog = false }) {
                        Text("取消")
                    }
                }
            }
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun ConceptItem(
    concept: Concept,
    isSelected: Boolean,
    isSelectionMode: Boolean,
    onSelect: () -> Unit,
    onClick: () -> Unit,
    onLongClick: () -> Unit,
    onToggleEnabled: (Boolean) -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .combinedClickable(
                onClick = {
                    if (isSelectionMode) {
                        onSelect()
                    } else {
                        onClick()
                    }
                },
                onLongClick = { onLongClick() }
            ),
        colors = CardDefaults.cardColors(
            containerColor = if (isSelected) {
                MaterialTheme.colorScheme.primaryContainer
            } else {
                MaterialTheme.colorScheme.surface
            }
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            if (isSelectionMode) {
                Checkbox(
                    checked = isSelected,
                    onCheckedChange = { onSelect() }
                )
                Spacer(modifier = Modifier.width(16.dp))
            }
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        concept.title,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Icon(
                        imageVector = if (concept.isEnabled) Icons.Default.CheckCircle else Icons.Default.RadioButtonUnchecked,
                        contentDescription = if (concept.isEnabled) "已启用" else "已禁用",
                        tint = if (concept.isEnabled) {
                            MaterialTheme.colorScheme.primary
                        } else {
                            MaterialTheme.colorScheme.onSurfaceVariant
                        },
                        modifier = Modifier.size(16.dp)
                    )
                }
                val categoryInfo = mutableListOf<String>()
                if (concept.category.isNotEmpty()) categoryInfo.add(concept.category)
                if (concept.subject.isNotEmpty()) categoryInfo.add(concept.subject)
                if (concept.subChapter.isNotEmpty()) categoryInfo.add(concept.subChapter)

                if (categoryInfo.isNotEmpty()) {
                    Text(
                        categoryInfo.joinToString(" - "),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
            if (!isSelectionMode) {
                // 启用/禁用切换按钮
                Switch(
                    checked = concept.isEnabled,
                    onCheckedChange = onToggleEnabled,
                    modifier = Modifier.padding(end = 8.dp)
                )
                Icon(
                    Icons.Default.ChevronRight,
                    contentDescription = "编辑",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
