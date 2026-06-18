package com.dailyread.app.ui.screens.concept

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
fun ConceptScreen(
    onNavigateToBottomNav: (String) -> Unit,
    onNavigateToManage: () -> Unit,
    onNavigateToEdit: (Long) -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ConceptViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.loadRandomConcept()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("背概念") },
                actions = {
                    if (uiState.randomConcept != null) {
                        IconButton(onClick = {
                            uiState.randomConcept?.id?.let { onNavigateToEdit(it) }
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
                currentRoute = "concept",
                onNavigate = onNavigateToBottomNav
            )
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { viewModel.loadRandomConcept() }
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
            uiState.randomConcept == null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(paddingValues),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(
                            "暂无概念数据",
                            style = MaterialTheme.typography.titleLarge,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            "请添加概念数据",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
            else -> {
                val concept = uiState.randomConcept!!
                val orientation = context.resources.configuration.orientation
                if (orientation == Configuration.ORIENTATION_PORTRAIT) {
                    PortraitLayout(
                        concept = concept,
                        paddingValues = paddingValues
                    )
                } else {
                    LandscapeLayout(
                        concept = concept,
                        paddingValues = paddingValues
                    )
                }
            }
        }
    }
}

@Composable
private fun PortraitLayout(
    concept: com.dailyread.app.data.local.database.entities.Concept,
    paddingValues: PaddingValues
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(paddingValues)
            .padding(16.dp)
            .verticalScroll(rememberScrollState())
    ) {
        ConceptInfo(concept = concept)

        if (!concept.imagePath.isNullOrEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            ConceptImage(imagePath = concept.imagePath)
        }
    }
}

@Composable
private fun LandscapeLayout(
    concept: com.dailyread.app.data.local.database.entities.Concept,
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
            ConceptInfo(concept = concept)
        }

        if (!concept.imagePath.isNullOrEmpty()) {
            Spacer(modifier = Modifier.width(16.dp))
            Column(
                modifier = Modifier.weight(1f),
                horizontalAlignment = Alignment.CenterHorizontally
            ) {
                ConceptImage(imagePath = concept.imagePath)
            }
        }
    }
}

@Composable
private fun ConceptInfo(concept: com.dailyread.app.data.local.database.entities.Concept) {
    Column(modifier = Modifier.fillMaxWidth()) {
        Text(
            concept.title,
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold,
            color = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.height(8.dp))

        val categoryInfo = mutableListOf<String>()
        if (concept.subject.isNotEmpty()) categoryInfo.add(concept.subject)
        if (concept.category.isNotEmpty()) categoryInfo.add(concept.category)
        if (concept.subChapter.isNotEmpty()) categoryInfo.add(concept.subChapter)

        if (categoryInfo.isNotEmpty()) {
            Text(
                categoryInfo.joinToString(" - "),
                style = MaterialTheme.typography.titleMedium,
                fontStyle = FontStyle.Italic,
                color = MaterialTheme.colorScheme.secondary
            )
        }

        if (concept.content.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                concept.content,
                style = MaterialTheme.typography.bodyLarge
            )
        }

        if (concept.note.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                "备注：${concept.note}",
                style = MaterialTheme.typography.bodyLarge,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}

@Composable
private fun ConceptImage(imagePath: String) {
    val context = LocalContext.current
    val file = File(imagePath)

    if (file.exists()) {
        AsyncImage(
            model = ImageRequest.Builder(context)
                .data(file)
                .build(),
            contentDescription = "概念图片",
            modifier = Modifier
                .fillMaxWidth()
                .aspectRatio(1f),
            contentScale = androidx.compose.ui.layout.ContentScale.Fit
        )
    }
}
