package com.dailyread.app.ui.screens.concept

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Image
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import coil.request.ImageRequest
import androidx.hilt.navigation.compose.hiltViewModel
import java.io.File

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddConceptScreen(
    conceptId: Long?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ConceptViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.editUiState.collectAsState()

    var subject by remember { mutableStateOf("") }
    var category by remember { mutableStateOf("") }
    var subChapter by remember { mutableStateOf("") }
    var title by remember { mutableStateOf("") }
    var content by remember { mutableStateOf("") }
    var imagePath by remember { mutableStateOf<String?>(null) }
    var note by remember { mutableStateOf("") }
    var isEnabled by remember { mutableStateOf(true) }

    LaunchedEffect(conceptId) {
        if (conceptId != null) {
            viewModel.loadConceptById(conceptId)
        } else {
            viewModel.clearEditState()
        }
    }

    LaunchedEffect(uiState.concept) {
        uiState.concept?.let { cpt ->
            subject = cpt.subject
            category = cpt.category
            subChapter = cpt.subChapter
            title = cpt.title
            content = cpt.content
            imagePath = cpt.imagePath
            note = cpt.note
            isEnabled = cpt.isEnabled
        }
    }

    val pickImageLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            try {
                val inputStream = context.contentResolver.openInputStream(it)
                val fileName = "concept_${System.currentTimeMillis()}.jpg"
                val file = File(context.filesDir, fileName)
                inputStream?.use { input ->
                    file.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                imagePath = file.absolutePath
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (conceptId == null) "添加概念" else "编辑概念") },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                }
            )
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
        } else {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues)
                    .verticalScroll(rememberScrollState())
                    .padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                OutlinedTextField(
                    value = subject,
                    onValueChange = { subject = it },
                    label = { Text("科目") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = category,
                    onValueChange = { category = it },
                    label = { Text("分类") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = subChapter,
                    onValueChange = { subChapter = it },
                    label = { Text("子章节") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = title,
                    onValueChange = { title = it },
                    label = { Text("标题 *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = content,
                    onValueChange = { content = it },
                    label = { Text("内容") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 5,
                    maxLines = 15
                )

                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            "图片",
                            style = MaterialTheme.typography.titleMedium
                        )

                        if (imagePath != null) {
                            val file = File(imagePath!!)
                            if (file.exists()) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .aspectRatio(1f)
                                        .clip(RoundedCornerShape(8.dp))
                                ) {
                                    AsyncImage(
                                        model = ImageRequest.Builder(context)
                                            .data(file)
                                            .build(),
                                        contentDescription = "概念图片",
                                        contentScale = ContentScale.Fit,
                                        modifier = Modifier.fillMaxSize()
                                    )
                                }
                                TextButton(
                                    onClick = { imagePath = null }
                                ) {
                                    Text("移除图片")
                                }
                            }
                        } else {
                            OutlinedButton(
                                onClick = {
                                    pickImageLauncher.launch("image/*")
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Icon(Icons.Default.Image, contentDescription = null)
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("选择图片")
                            }
                        }
                    }
                }

                OutlinedTextField(
                    value = note,
                    onValueChange = { note = it },
                    label = { Text("备注") },
                    modifier = Modifier.fillMaxWidth()
                )

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Switch(
                        checked = isEnabled,
                        onCheckedChange = { isEnabled = it }
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("启用此概念")
                }

                Button(
                    onClick = {
                        viewModel.saveConcept(
                            subject = subject,
                            category = category,
                            subChapter = subChapter,
                            title = title,
                            content = content,
                            imagePath = imagePath,
                            note = note,
                            isEnabled = isEnabled,
                            id = conceptId
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = title.isNotBlank()
                ) {
                    Text("保存")
                }
            }
        }

        LaunchedEffect(uiState.navigateBack) {
            if (uiState.navigateBack) {
                android.widget.Toast.makeText(
                    context,
                    if (conceptId != null) "保存成功" else "添加成功",
                    android.widget.Toast.LENGTH_SHORT
                ).show()
                onBack()
            }
        }
    }
}
