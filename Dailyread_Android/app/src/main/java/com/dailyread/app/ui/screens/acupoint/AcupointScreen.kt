package com.dailyread.app.ui.screens.acupoint

import android.content.res.Configuration
import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Edit
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.graphics.drawable.toBitmap
import androidx.hilt.navigation.compose.hiltViewModel
import coil.compose.AsyncImage
import coil.imageLoader
import coil.request.ImageRequest
import com.dailyread.app.ui.components.BottomNavigationBar
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AcupointScreen(
    onNavigateToBottomNav: (String) -> Unit,
    onNavigateToManage: () -> Unit,
    onNavigateToEdit: (Long) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: AcupointViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.loadRandomAcupoint()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("背穴位") },
                actions = {
                    if (uiState.randomAcupoint != null) {
                        IconButton(onClick = { 
                            uiState.randomAcupoint?.id?.let { onNavigateToEdit(it) }
                        }) {
                            Icon(Icons.Default.Edit, contentDescription = "编辑")
                        }
                    }
                    IconButton(onClick = onNavigateToManage) {
                        Icon(Icons.Default.Settings, contentDescription = "管理")
                    }
                }
            )
        },
        bottomBar = {
            BottomNavigationBar(
                currentRoute = "acupoint",
                onNavigate = onNavigateToBottomNav
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.loadRandomAcupoint() }
            ) {
                Icon(Icons.Default.Refresh, contentDescription = "换一个")
            }
        },
        modifier = modifier
    ) { paddingValues ->
        when {
            uiState.isLoading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            uiState.randomAcupoint == null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "暂无穴位数据",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            "请添加穴位数据",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            else -> {
                val acupoint = uiState.randomAcupoint!!
                val orientation = context.resources.configuration.orientation
                if (orientation == Configuration.ORIENTATION_PORTRAIT) {
                    PortraitLayout(
                        acupoint = acupoint,
                        paddingValues = paddingValues
                    )
                } else {
                    LandscapeLayout(
                        acupoint = acupoint,
                        paddingValues = paddingValues
                    )
                }
            }
        }
    }
}

@Composable
private fun PortraitLayout(
    acupoint: com.dailyread.app.data.local.database.entities.Acupoint,
    paddingValues: PaddingValues
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(paddingValues)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        AcupointInfo(acupoint = acupoint)

        if (!acupoint.locationImagePath.isNullOrEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            LocationImage(imagePath = acupoint.locationImagePath)
        }
    }
}

@Composable
private fun LandscapeLayout(
    acupoint: com.dailyread.app.data.local.database.entities.Acupoint,
    paddingValues: PaddingValues
) {
    Row(
        modifier = Modifier
            .fillMaxSize()
            .padding(paddingValues)
            .padding(16.dp)
    ) {
        Column(
            modifier = Modifier
                .weight(2f)
                .verticalScroll(rememberScrollState())
        ) {
            AcupointInfo(acupoint = acupoint)
        }

        if (!acupoint.locationImagePath.isNullOrEmpty()) {
            Spacer(modifier = Modifier.width(16.dp))
            Column(
                modifier = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                LocationImage(imagePath = acupoint.locationImagePath)
            }
        }
    }
}

@Composable
private fun AcupointInfo(acupoint: com.dailyread.app.data.local.database.entities.Acupoint) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            acupoint.acupoint,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            acupoint.meridian,
            style = MaterialTheme.typography.titleMedium,
            fontStyle = FontStyle.Italic,
            color = MaterialTheme.colorScheme.secondary
        )

        if (acupoint.acupointProperty.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "穴性：${acupoint.acupointProperty}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.location.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "定位：${acupoint.location}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.function.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "功效：${acupoint.function}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.indications.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "主治：${acupoint.indications}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.anatomy.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "解剖：${acupoint.anatomy}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.operation.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "操作：${acupoint.operation}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.contraindications.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "禁忌：${acupoint.contraindications}",
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (acupoint.note.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "备注：${acupoint.note}",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun LocationImage(imagePath: String) {
    val context = LocalContext.current
    val file = File(imagePath)

    if (file.exists()) {
        AsyncImage(
            model = ImageRequest.Builder(context)
                .data(file)
                .build(),
            contentDescription = "穴位定位图",
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f),
            contentScale = androidx.compose.ui.layout.ContentScale.Fit
        )
    }
}
