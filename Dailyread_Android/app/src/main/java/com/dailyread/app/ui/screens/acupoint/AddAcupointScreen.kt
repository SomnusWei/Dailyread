package com.dailyread.app.ui.screens.acupoint

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
fun AddAcupointScreen(
    acupointId: Long?,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: AcupointViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.editUiState.collectAsState()
    
    var acupoint by remember { mutableStateOf("") }
    var meridian by remember { mutableStateOf("") }
    var acupointProperty by remember { mutableStateOf("") }
    var location by remember { mutableStateOf("") }
    var function by remember { mutableStateOf("") }
    var indications by remember { mutableStateOf("") }
    var anatomy by remember { mutableStateOf("") }
    var operation by remember { mutableStateOf("") }
    var contraindications by remember { mutableStateOf("") }
    var locationImagePath by remember { mutableStateOf<String?>(null) }
    var note by remember { mutableStateOf("") }

    LaunchedEffect(acupointId) {
        if (acupointId != null) {
            viewModel.loadAcupointById(acupointId)
        } else {
            viewModel.clearEditState()
        }
    }

    LaunchedEffect(uiState.acupoint) {
        uiState.acupoint?.let { acp ->
            acupoint = acp.acupoint
            meridian = acp.meridian
            acupointProperty = acp.acupointProperty
            location = acp.location
            function = acp.function
            indications = acp.indications
            anatomy = acp.anatomy
            operation = acp.operation
            contraindications = acp.contraindications
            locationImagePath = acp.locationImagePath
            note = acp.note
        }
    }

    val pickImageLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            try {
                val inputStream = context.contentResolver.openInputStream(it)
                val fileName = "acupoint_${System.currentTimeMillis()}.jpg"
                val file = File(context.filesDir, fileName)
                inputStream?.use { input ->
                    file.outputStream().use { output ->
                        input.copyTo(output)
                    }
                }
                locationImagePath = file.absolutePath
            } catch (e: Exception) {
                e.printStackTrace()
            }
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(if (acupointId == null) "添加穴位" else "编辑穴位") },
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
                    value = acupoint,
                    onValueChange = { acupoint = it },
                    label = { Text("穴位名称 *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = meridian,
                    onValueChange = { meridian = it },
                    label = { Text("经络 *") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = acupointProperty,
                    onValueChange = { acupointProperty = it },
                    label = { Text("穴性") },
                    modifier = Modifier.fillMaxWidth(),
                    singleLine = true
                )

                OutlinedTextField(
                    value = location,
                    onValueChange = { location = it },
                    label = { Text("定位") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = function,
                    onValueChange = { function = it },
                    label = { Text("功效") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = indications,
                    onValueChange = { indications = it },
                    label = { Text("主治") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = anatomy,
                    onValueChange = { anatomy = it },
                    label = { Text("解剖") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = operation,
                    onValueChange = { operation = it },
                    label = { Text("操作") },
                    modifier = Modifier.fillMaxWidth()
                )

                OutlinedTextField(
                    value = contraindications,
                    onValueChange = { contraindications = it },
                    label = { Text("禁忌") },
                    modifier = Modifier.fillMaxWidth()
                )

                Card(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            "穴位定位图",
                            style = MaterialTheme.typography.titleMedium
                        )
                        
                        if (locationImagePath != null) {
                            val file = File(locationImagePath!!)
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
                                        contentDescription = "穴位定位图",
                                        contentScale = ContentScale.Fit,
                                        modifier = Modifier.fillMaxSize()
                                    )
                                }
                                TextButton(
                                    onClick = { locationImagePath = null }
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

                Button(
                    onClick = {
                        viewModel.saveAcupoint(
                            acupoint = acupoint,
                            meridian = meridian,
                            acupointProperty = acupointProperty,
                            location = location,
                            function = function,
                            indications = indications,
                            anatomy = anatomy,
                            operation = operation,
                            contraindications = contraindications,
                            locationImagePath = locationImagePath,
                            note = note,
                            id = acupointId
                        )
                    },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = acupoint.isNotBlank() && meridian.isNotBlank()
                ) {
                    Text("保存")
                }
            }
        }

        LaunchedEffect(uiState.navigateBack) {
            if (uiState.navigateBack) {
                android.widget.Toast.makeText(
                    context,
                    if (acupointId == null) "添加成功" else "保存成功",
                    android.widget.Toast.LENGTH_SHORT
                ).show()
                onBack()
            }
        }
    }
}
