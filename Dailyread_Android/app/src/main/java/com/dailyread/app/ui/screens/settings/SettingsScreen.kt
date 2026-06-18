package com.dailyread.app.ui.screens.settings

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Cloud
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Upload
import androidx.compose.material.icons.filled.Visibility
import androidx.compose.material.icons.filled.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import com.dailyread.app.ui.components.BottomNavigationBar
import com.dailyread.app.ui.components.Heatmap
import com.dailyread.app.ui.screens.stats.StatsViewModel
import java.time.LocalDate

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    onBack: () -> Unit,
    onNavigateToBottomNav: (String) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: SettingsViewModel = hiltViewModel(),
    statsViewModel: StatsViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()
    val statsUiState by statsViewModel.uiState.collectAsState()
    var showResetConfirmDialog by remember { mutableStateOf(false) }
    var showImportResultDialog by remember { mutableStateOf<String?>(null) }
    var isBackPressed by remember { mutableStateOf(false) }
    var showWebDavConfigDialog by remember { mutableStateOf(false) }
    var showExportOptionsDialog by remember { mutableStateOf(false) }
    var hasLoadedStats by remember { mutableStateOf(false) }
    var selectedExportType by remember { mutableStateOf<com.dailyread.app.domain.usecase.ExportType?>(null) }
    
    LaunchedEffect(Unit) {
        try {
            kotlinx.coroutines.delay(100)
            if (!hasLoadedStats) {
                hasLoadedStats = true
                statsViewModel.loadData()
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
    
    val pickFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri ->
        uri?.let {
            val filePath = try {
                val inputStream = context.contentResolver.openInputStream(it)
                inputStream?.let { stream ->
                    val tempFile = java.io.File(context.cacheDir, "import_temp.json")
                    stream.use { input ->
                        tempFile.outputStream().use { output ->
                            input.copyTo(output)
                        }
                    }
                    tempFile.absolutePath
                }
            } catch (e: Exception) {
                null
            }
            
            filePath?.let { path ->
                viewModel.importData(path)
            } ?: run {
                android.widget.Toast.makeText(
                    context,
                    "无法读取文件",
                    android.widget.Toast.LENGTH_SHORT
                ).show()
            }
        }
    }

    val selectFolderLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.OpenDocumentTree()
    ) { uri ->
        uri?.let { treeUri ->
            context.contentResolver.takePersistableUriPermission(
                treeUri,
                android.content.Intent.FLAG_GRANT_READ_URI_PERMISSION or
                        android.content.Intent.FLAG_GRANT_WRITE_URI_PERMISSION
            )
            
            selectedExportType?.let { exportType ->
                viewModel.exportDataWithUri(exportType, treeUri)
            }
        }
        selectedExportType = null
    }

    LaunchedEffect(uiState.showToast) {
        if (uiState.showToast != null) {
            val toast = uiState.showToast!!
            if (toast.contains("\n")) {
                showImportResultDialog = toast
            } else {
                android.widget.Toast.makeText(
                    context,
                    toast,
                    android.widget.Toast.LENGTH_SHORT
                ).show()
            }
            viewModel.clearToast()
        }
    }

    showImportResultDialog?.let { message ->
        AlertDialog(
            onDismissRequest = { showImportResultDialog = null },
            title = { Text("导入结果") },
            text = {
                Column {
                    message.split("\n").forEach { line ->
                        Text(
                            line,
                            style = MaterialTheme.typography.bodyMedium,
                            modifier = Modifier.padding(vertical = 2.dp)
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showImportResultDialog = null }) {
                    Text("确定")
                }
            }
        )
    }

    if (showResetConfirmDialog) {
        AlertDialog(
            onDismissRequest = { showResetConfirmDialog = false },
            title = { Text("确认重置") },
            text = { Text("确定要重置今日阅读任务吗？系统将重新生成今日任务列表。") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.resetTodayTasks()
                        showResetConfirmDialog = false
                    }
                ) {
                    Text("确定")
                }
            },
            dismissButton = {
                TextButton(onClick = { showResetConfirmDialog = false }) {
                    Text("取消")
                }
            }
        )
    }

    if (showWebDavConfigDialog) {
        WebDavConfigDialog(
            initialServerUrl = uiState.webdavServerUrl,
            initialUsername = uiState.webdavUsername,
            initialPassword = uiState.webdavPassword,
            initialRemotePath = uiState.webdavRemotePath,
            onDismiss = { showWebDavConfigDialog = false },
            onSave = { serverUrl, username, password, remotePath ->
                viewModel.updateWebDavConfig(serverUrl, username, password, remotePath)
                showWebDavConfigDialog = false
            }
        )
    }

    if (showExportOptionsDialog) {
        ExportOptionsDialog(
            onDismiss = { showExportOptionsDialog = false },
            onExportAll = {
                selectedExportType = com.dailyread.app.domain.usecase.ExportType.ALL
                selectFolderLauncher.launch(null)
                showExportOptionsDialog = false
            },
            onExportArticles = {
                selectedExportType = com.dailyread.app.domain.usecase.ExportType.ARTICLES_ONLY
                selectFolderLauncher.launch(null)
                showExportOptionsDialog = false
            },
            onExportAcupoints = {
                selectedExportType = com.dailyread.app.domain.usecase.ExportType.ACUPOINTS_ONLY
                selectFolderLauncher.launch(null)
                showExportOptionsDialog = false
            },
            onExportConcepts = {
                selectedExportType = com.dailyread.app.domain.usecase.ExportType.CONCEPTS_ONLY
                selectFolderLauncher.launch(null)
                showExportOptionsDialog = false
            }
        )
    }

    if (uiState.showConflictDialog && uiState.currentConflict != null) {
        AlertDialog(
            onDismissRequest = { viewModel.dismissConflictDialog() },
            title = { Text("数据冲突") },
            text = {
                Column {
                    Text("检测到数据冲突，请选择保留哪个版本：")
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        "本地修改时间: ${uiState.currentConflict!!.localTimestamp}",
                        style = MaterialTheme.typography.bodySmall
                    )
                    Text(
                        "云端修改时间: ${uiState.currentConflict!!.remoteTimestamp}",
                        style = MaterialTheme.typography.bodySmall
                    )
                }
            },
            confirmButton = {
                TextButton(onClick = { viewModel.resolveConflict(useLocal = true) }) {
                    Text("使用本地版本")
                }
            },
            dismissButton = {
                TextButton(onClick = { viewModel.resolveConflict(useLocal = false) }) {
                    Text("使用云端版本")
                }
            }
        )
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("设置") },
                navigationIcon = {
                    IconButton(
                        onClick = {
                            if (!isBackPressed) {
                                isBackPressed = true
                                onBack()
                            }
                        },
                        enabled = !isBackPressed
                    ) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        },
        bottomBar = {
            BottomNavigationBar(
                currentRoute = "settings",
                onNavigate = onNavigateToBottomNav
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
            Text(
                "阅读设置",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text("每日阅读时间", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "${uiState.dailyMinutes} 分钟",
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Spacer(modifier = Modifier.weight(1f))
                        Button(onClick = { viewModel.updateDailyMinutes((uiState.dailyMinutes - 5).coerceAtLeast(5)) }) {
                            Text("-5")
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Button(onClick = { viewModel.updateDailyMinutes((uiState.dailyMinutes + 5).coerceAtMost(120)) }) {
                            Text("+5")
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text("目标完成率", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            "${uiState.targetCheckRate.toInt()}%",
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Spacer(modifier = Modifier.weight(1f))
                        Slider(
                            value = uiState.targetCheckRate,
                            onValueChange = {
                                viewModel.updateTargetCheckRate((it / 5f).toInt() * 5f)
                            },
                            valueRange = 5f..100f,
                            steps = 18,
                            modifier = Modifier.weight(1f)
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("保持屏幕常亮", style = MaterialTheme.typography.titleMedium)
                        Text(
                            "应用在前台时屏幕不会自动休眠",
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Switch(
                        checked = uiState.keepScreenOn,
                        onCheckedChange = { viewModel.updateKeepScreenOn(it) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                "数据管理",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Button(
                onClick = { showExportOptionsDialog = true },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("导出数据")
            }

            Spacer(modifier = Modifier.height(8.dp))

            Button(
                onClick = { 
                    pickFileLauncher.launch("application/json")
                },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("导入数据")
            }

            Spacer(modifier = Modifier.height(8.dp))
            
            Button(
                onClick = { showResetConfirmDialog = true },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.secondary
                )
            ) {
                Text(
                    text = if (uiState.isTasksLocked) "任务已锁定，点击重置" else "重置今日阅读任务",
                    modifier = Modifier.fillMaxWidth(),
                    textAlign = TextAlign.Center
                )
            }
            
            if (uiState.isTasksLocked) {
                Text(
                    "任务已锁定，将在次日00:01自动解锁",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                    modifier = Modifier.padding(top = 4.dp)
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                "WebDAV 同步",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("启用 WebDAV 同步", style = MaterialTheme.typography.titleMedium)
                            if (uiState.webdavEnabled && uiState.lastSyncTime != null) {
                                Text(
                                    "上次同步: ${uiState.lastSyncTime}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                        Switch(
                            checked = uiState.webdavEnabled,
                            onCheckedChange = { viewModel.toggleWebDavEnabled(it) }
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))
                        
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("自动同步", style = MaterialTheme.typography.titleMedium)
                            Text(
                                "在操作后自动上传数据到云端",
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        Switch(
                            checked = uiState.autoSyncWebDav,
                            onCheckedChange = { viewModel.updateAutoSyncWebDav(it) },
                            enabled = uiState.webdavEnabled
                        )
                    }
                    
                    if (uiState.webdavEnabled) {
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Text(
                            "同步内容设置",
                            style = MaterialTheme.typography.titleMedium
                        )
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("同步文章数据", style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    "同步和备份阅读文章",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                            Switch(
                                checked = uiState.syncArticlesEnabled,
                                onCheckedChange = { viewModel.updateSyncArticlesEnabled(it) }
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("同步穴位数据", style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    "同步和备份穴位信息",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                            Switch(
                                checked = uiState.syncAcupointsEnabled,
                                onCheckedChange = { viewModel.updateSyncAcupointsEnabled(it) }
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(8.dp))
                        
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("同步概念数据", style = MaterialTheme.typography.bodyMedium)
                                Text(
                                    "同步和备份概念笔记",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                            Switch(
                                checked = uiState.syncConceptsEnabled,
                                onCheckedChange = { viewModel.updateSyncConceptsEnabled(it) }
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        Button(
                            onClick = { showWebDavConfigDialog = true },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.Cloud, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("配置 WebDAV")
                        }

                        Spacer(modifier = Modifier.height(8.dp))

                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Button(
                                onClick = { viewModel.testWebDavConnection() },
                                modifier = Modifier.weight(1f),
                                enabled = !uiState.isSyncing
                            ) {
                                if (uiState.isSyncing) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(16.dp),
                                        strokeWidth = 2.dp
                                    )
                                } else {
                                    Text("测试连接")
                                }
                            }
                            
                            Button(
                                onClick = { viewModel.syncFromCloud() },
                                modifier = Modifier.weight(1f),
                                enabled = !uiState.isSyncing
                            ) {
                                if (uiState.isSyncing) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(16.dp),
                                        strokeWidth = 2.dp
                                    )
                                } else {
                                    Icon(Icons.Default.Download, contentDescription = null)
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("下载")
                                }
                            }
                            
                            Button(
                                onClick = { viewModel.syncToCloud() },
                                modifier = Modifier.weight(1f),
                                enabled = !uiState.isSyncing
                            ) {
                                if (uiState.isSyncing) {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(16.dp),
                                        strokeWidth = 2.dp
                                    )
                                } else {
                                    Icon(Icons.Default.Upload, contentDescription = null)
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Text("上传")
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Text(
                "阅读统计",
                style = MaterialTheme.typography.headlineSmall,
                modifier = Modifier.padding(bottom = 16.dp)
            )

            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp)
            ) {
                Column(
                    modifier = Modifier.padding(16.dp)
                ) {
                    Text(
                        "阅读热力图",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = androidx.compose.ui.text.font.FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 12.dp)
                    )

                    Heatmap(
                        year = LocalDate.now().year,
                        checkInData = statsUiState.heatmapData,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(16.dp))

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(
                            "总阅读文章: ${statsUiState.totalArticles}",
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Text(
                            "总打卡次数: ${statsUiState.totalCheckIns}",
                            style = MaterialTheme.typography.bodyLarge
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            Text(
                text = "版本号: 1.41",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.fillMaxWidth().wrapContentWidth(Alignment.CenterHorizontally)
            )
        }
    }
}

@Composable
fun ExportOptionsDialog(
    onDismiss: () -> Unit,
    onExportAll: () -> Unit,
    onExportArticles: () -> Unit,
    onExportAcupoints: () -> Unit,
    onExportConcepts: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("选择导出类型") },
        text = {
            Column(
                modifier = Modifier.fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                OutlinedButton(
                    onClick = onExportAll,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("导出全部数据")
                }
                
                OutlinedButton(
                    onClick = onExportArticles,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("仅导出文章数据")
                }
                
                OutlinedButton(
                    onClick = onExportAcupoints,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("仅导出穴位数据")
                }
                
                OutlinedButton(
                    onClick = onExportConcepts,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("仅导出概念数据")
                }
            }
        },
        confirmButton = {},
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}

@Composable
fun WebDavConfigDialog(
    initialServerUrl: String,
    initialUsername: String,
    initialPassword: String,
    initialRemotePath: String,
    onDismiss: () -> Unit,
    onSave: (String, String, String, String) -> Unit
) {
    var serverUrl by remember { mutableStateOf(initialServerUrl) }
    var username by remember { mutableStateOf(initialUsername) }
    var password by remember { mutableStateOf(initialPassword) }
    var remotePath by remember { mutableStateOf(initialRemotePath) }
    var passwordVisible by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("WebDAV 配置") },
        text = {
            Column {
                OutlinedTextField(
                    value = serverUrl,
                    onValueChange = { serverUrl = it },
                    label = { Text("服务器地址") },
                    placeholder = { Text("http://192.168.1.100:8080") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Uri)
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                OutlinedTextField(
                    value = username,
                    onValueChange = { username = it },
                    label = { Text("用户名") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                OutlinedTextField(
                    value = password,
                    onValueChange = { password = it },
                    label = { Text("密码") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true,
                    visualTransformation = if (passwordVisible) VisualTransformation.None else PasswordVisualTransformation(),
                    trailingIcon = {
                        IconButton(onClick = { passwordVisible = !passwordVisible }) {
                            Icon(
                                imageVector = if (passwordVisible) Icons.Default.VisibilityOff else Icons.Default.Visibility,
                                contentDescription = if (passwordVisible) "隐藏密码" else "显示密码"
                            )
                        }
                    }
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                OutlinedTextField(
                    value = remotePath,
                    onValueChange = { remotePath = it },
                    label = { Text("同步目录") },
                    placeholder = { Text("/DailyRead") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text(
                    "提示：服务器地址需要包含协议（http/https）和端口号",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    onSave(serverUrl.trim(), username.trim(), password, remotePath.trim().ifEmpty { "/DailyRead" })
                },
                enabled = serverUrl.isNotBlank() && username.isNotBlank()
            ) {
                Text("保存")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("取消")
            }
        }
    )
}
