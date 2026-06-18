package com.dailyread.app.ui.screens.reader
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.TextDecrease
import androidx.compose.material.icons.filled.TextIncrease
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReaderScreen(
    articleId: Long,
    onBack: () -> Unit,
    modifier: Modifier = Modifier,
    viewModel: ReaderViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()
    var showBars by remember { mutableStateOf(false) }

    LaunchedEffect(articleId) {
        viewModel.loadArticle(articleId)
        viewModel.startTimer()
    }

    DisposableEffect(Unit) {
        onDispose {
            viewModel.stopTimer()
        }
    }

    Box(modifier = modifier.fillMaxSize()) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .clickable(
                    interactionSource = remember { MutableInteractionSource() },
                    indication = null
                ) {
                    showBars = !showBars
                }
                .padding(16.dp)
        ) {
            uiState.article?.let { article ->
                Text(
                    article.title,
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    textAlign = TextAlign.Center,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis,
                    modifier = Modifier.fillMaxWidth()
                )

                Spacer(modifier = Modifier.height(24.dp))

                Column(
                    modifier = Modifier
                        .weight(1f)
                        .verticalScroll(rememberScrollState())
                ) {
                    Text(
                        article.content,
                        fontSize = uiState.fontSize.sp,
                        fontWeight = if (article.isBold) FontWeight.Bold else FontWeight.Normal,
                        color = androidx.compose.ui.graphics.Color(
                            android.graphics.Color.parseColor(article.fontColor)
                        ),
                        lineHeight = (uiState.fontSize * 1.8).sp
                    )

                    Spacer(modifier = Modifier.height(32.dp))

                    Button(
                        onClick = { viewModel.checkIn() },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !uiState.isCheckedIn,
                        colors = ButtonDefaults.buttonColors(
                            containerColor = if (uiState.isCheckedIn) {
                                MaterialTheme.colorScheme.secondary
                            } else {
                                MaterialTheme.colorScheme.primary
                            }
                        )
                    ) {
                        Text(
                            if (uiState.isCheckedIn) "✓ 已打卡" else "完成阅读并打卡",
                            style = MaterialTheme.typography.titleMedium
                        )
                    }

                    Spacer(modifier = Modifier.height(48.dp))
                }
            } ?: run {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
        }

        LaunchedEffect(uiState.showToast) {
            if (uiState.showToast != null) {
                android.widget.Toast.makeText(
                    context,
                    uiState.showToast,
                    android.widget.Toast.LENGTH_SHORT
                ).show()
                viewModel.clearToast()
            }
        }

        AnimatedVisibility(
            visible = showBars,
            modifier = Modifier.align(Alignment.TopCenter),
            enter = slideInVertically { -it } + fadeIn(),
            exit = slideOutVertically { -it } + fadeOut()
        ) {
            TopAppBar(
                title = {
                    Text(
                        uiState.article?.title ?: "阅读",
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                },
                actions = {
                    Text(
                        formatReadingTime(uiState.readingTimeSeconds),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f)
                )
            )
        }

        AnimatedVisibility(
            visible = showBars,
            modifier = Modifier.align(Alignment.BottomCenter),
            enter = slideInVertically { it } + fadeIn(),
            exit = slideOutVertically { it } + fadeOut()
        ) {
            Surface(
                shadowElevation = 8.dp,
                color = MaterialTheme.colorScheme.surface.copy(alpha = 0.95f),
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable(
                        interactionSource = remember { MutableInteractionSource() },
                        indication = null
                    ) { }
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                        .navigationBarsPadding()
                ) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(
                            onClick = { viewModel.decreaseFontSize() },
                            modifier = Modifier.size(48.dp)
                        ) {
                            Icon(
                                Icons.Default.TextDecrease,
                                contentDescription = "减小字体",
                                modifier = Modifier.size(28.dp)
                            )
                        }

                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text(
                                "字体大小: ${uiState.fontSize}sp",
                                style = MaterialTheme.typography.bodyMedium
                            )
                            TextButton(
                                onClick = { viewModel.resetFontSize() }
                            ) {
                                Icon(
                                    Icons.Default.Refresh,
                                    contentDescription = "重置字体",
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("重置")
                            }
                        }

                        IconButton(
                            onClick = { viewModel.increaseFontSize() },
                            modifier = Modifier.size(48.dp)
                        ) {
                            Icon(
                                Icons.Default.TextIncrease,
                                contentDescription = "增大字体",
                                modifier = Modifier.size(28.dp)
                            )
                        }
                    }
                }
            }
        }
    }
}

private fun formatReadingTime(totalSeconds: Int): String {
    val hours = totalSeconds / 3600
    val minutes = (totalSeconds % 3600) / 60
    val seconds = totalSeconds % 60
    
    return if (hours > 0) {
        String.format("%d:%02d:%02d", hours, minutes, seconds)
    } else {
        String.format("%02d:%02d", minutes, seconds)
    }
}
