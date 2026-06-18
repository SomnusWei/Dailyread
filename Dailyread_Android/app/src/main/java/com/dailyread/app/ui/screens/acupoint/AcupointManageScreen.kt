package com.dailyread.app.ui.screens.acupoint

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
import com.dailyread.app.data.local.database.entities.Acupoint
import com.dailyread.app.ui.components.BottomNavigationBar

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AcupointManageScreen(
    onNavigateToBottomNav: (String) -> Unit,
    onNavigateToAdd: () -> Unit,
    onNavigateToEdit: (Long) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: AcupointViewModel = hiltViewModel()
) {
    val uiState by viewModel.manageUiState.collectAsState()
    var showDeleteConfirmDialog by remember { mutableStateOf(false) }
    var showSearchDialog by remember { mutableStateOf(false) }
    var showFilterDialog by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        viewModel.loadAllAcupoints()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { 
                    Text(if (uiState.selectedAcupoints.isNotEmpty()) {
                        "已选择 ${uiState.selectedAcupoints.size} 项"
                    } else {
                        "穴位管理"
                    })
                },
                actions = {
                    if (uiState.selectedAcupoints.isNotEmpty()) {
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
                currentRoute = "acupoint_manage",
                onNavigate = onNavigateToBottomNav
            )
        },
        floatingActionButton = {
            if (uiState.selectedAcupoints.isEmpty()) {
                FloatingActionButton(onClick = onNavigateToAdd) {
                    Icon(Icons.Default.Add, contentDescription = "添加穴位")
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
        } else if (uiState.acupoints.isEmpty()) {
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
                        "暂无穴位数据",
                        style = MaterialTheme.typography.titleLarge,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "点击右下角按钮添加穴位",
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
                items(uiState.acupoints, key = { it.id }) { acupoint ->
                    AcupointItem(
                        acupoint = acupoint,
                        isSelected = uiState.selectedAcupoints.contains(acupoint.id),
                        isSelectionMode = uiState.selectedAcupoints.isNotEmpty(),
                        onSelect = { viewModel.toggleSelectAcupoint(acupoint.id) },
                        onClick = { onNavigateToEdit(acupoint.id) },
                        onLongClick = { viewModel.toggleSelectAcupoint(acupoint.id) }
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
                Text("确定要删除选中的 ${uiState.selectedAcupoints.size} 个穴位吗？") 
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
            title = { Text("搜索穴位") },
            text = {
                OutlinedTextField(
                    value = searchQuery,
                    onValueChange = { searchQuery = it },
                    label = { Text("穴位名称") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.searchAcupoints(searchQuery)
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
        var selectedMeridian by remember { mutableStateOf(uiState.selectedMeridian) }
        // 计算每个经络的穴位数量
        val meridianCounts = remember(uiState.acupoints) {
            uiState.acupoints.groupBy { it.meridian }
                .mapValues { it.value.size }
        }
        val totalCount = uiState.acupoints.size
        AlertDialog(
            onDismissRequest = { showFilterDialog = false },
            title = { Text("按经络筛选") },
            text = {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        RadioButton(
                            selected = selectedMeridian == null,
                            onClick = { selectedMeridian = null }
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Row(
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text("全部", style = MaterialTheme.typography.bodyLarge)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                "($totalCount)",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }
                    uiState.meridians.forEach { meridian ->
                        val count = meridianCounts[meridian] ?: 0
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = selectedMeridian == meridian,
                                onClick = { selectedMeridian = meridian }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Row(
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(meridian, style = MaterialTheme.typography.bodyLarge)
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
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.filterByMeridian(selectedMeridian)
                        showFilterDialog = false
                    }
                ) {
                    Text("确定")
                }
            },
            dismissButton = {
                TextButton(onClick = { showFilterDialog = false }) {
                    Text("取消")
                }
            }
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
fun AcupointItem(
    acupoint: Acupoint,
    isSelected: Boolean,
    isSelectionMode: Boolean,
    onSelect: () -> Unit,
    onClick: () -> Unit,
    onLongClick: () -> Unit
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
                Text(
                    acupoint.acupoint,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = androidx.compose.ui.text.font.FontWeight.Bold
                )
                Text(
                    acupoint.meridian,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
            if (!isSelectionMode) {
                Icon(
                    Icons.Default.ChevronRight,
                    contentDescription = "编辑",
                    tint = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
