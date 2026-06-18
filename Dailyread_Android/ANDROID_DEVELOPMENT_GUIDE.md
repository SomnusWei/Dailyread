# 轻量阅读 - Android 开发指南

## 目录
1. [项目概述](#项目概述)
2. [技术选型](#技术选型)
3. [项目架构](#项目架构)
4. [数据库设计](#数据库设计)
5. [核心功能实现](#核心功能实现)
6. [云同步集成](#云同步集成)
7. [UI设计规范](#ui设计规范)
8. [开发步骤详解](#开发步骤详解)

---

## 项目概述

### 项目目标
将现有的 Python 桌面版「轻量阅读」移植到 Android 平台，保持以下核心特性：
- 极速启动（< 2秒）
- 极简设计
- 智能任务推荐
- 打卡系统
- 热力图统计
- 与桌面版/小程序数据云同步

### 功能清单

| 功能模块 | 优先级 | 说明 |
|---------|--------|------|
| 文章管理 | P0 | 添加、编辑、删除、启用/禁用文章 |
| 每日任务 | P0 | 智能推荐今日阅读任务 |
| 文章阅读 | P0 | 阅读器、支持自定义字体 |
| 打卡系统 | P0 | 每日打卡、防重复 |
| 热力图 | P1 | 年度阅读热力图 |
| 统计数据 | P1 | 月度打卡、总字数 |
| 设置 | P1 | 阅读时长、主题、云同步 |
| 补打卡 | P2 | 历史日期补打卡 |
| 云同步 | P2 | 与桌面/小程序数据同步 |

---

## 技术选型

### 推荐方案：Kotlin + Jetpack Compose

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Kotlin | 现代 Android 开发首选 |
| UI框架 | Jetpack Compose | 声明式 UI，开发效率高 |
| 架构 | MVVM + Clean Architecture | 清晰的代码组织 |
| 本地数据库 | Room | SQLite ORM，Jetpack 组件 |
| 异步处理 | Kotlin Coroutines + Flow | 轻量高效 |
| 依赖注入 | Hilt | Google 推荐 |
| 云服务 | 微信云开发 HTTP API | 与小程序共用后端 |
| 图表库 | Compose 自定义绘制 / Vico | 热力图轻量实现 |

### 备选方案：Flutter

| 组件 | 选型 | 说明 |
|------|------|------|
| 语言 | Dart | Flutter 专用语言 |
| UI框架 | Flutter | 跨平台，一套代码多端运行 |
| 状态管理 | Provider / Riverpod | 轻量高效 |
| 本地数据库 | sqflite | SQLite 插件 |
| 云服务 | 微信云开发 HTTP API | 与小程序共用后端 |

---

## 项目架构（Kotlin + Compose 方案）

### 目录结构

```
app/
├── data/                     # 数据层
│   ├── local/               # 本地数据
│   │   ├── database/        # Room 数据库
│   │   │   ├── AppDatabase.kt
│   │   │   ├── entities/
│   │   │   │   ├── Content.kt
│   │   │   │   ├── ContentCheckIn.kt
│   │   │   │   └── Config.kt
│   │   │   └── dao/
│   │   │       ├── ContentDao.kt
│   │   │       ├── ContentCheckInDao.kt
│   │   │       └── ConfigDao.kt
│   │   └── preferences/     # DataStore（配置存储）
│   │       └── AppPreferences.kt
│   ├── remote/              # 远程数据（云同步）
│   │   ├── api/
│   │   │   └── CloudApi.kt
│   │   └── model/
│   │       ├── CloudArticle.kt
│   │       └── CloudReadingRecord.kt
│   └── repository/          # 数据仓库
│       ├── ContentRepository.kt
│       ├── CheckInRepository.kt
│       └── ConfigRepository.kt
│
├── domain/                   # 领域层
│   ├── model/
│   │   ├── Article.kt
│   │   ├── CheckInRecord.kt
│   │   └── AppConfig.kt
│   └── usecase/
│       ├── GetTodayTasksUseCase.kt
│       ├── AddArticleUseCase.kt
│       ├── CheckInArticleUseCase.kt
│       ├── GetHeatmapDataUseCase.kt
│       └── SyncDataUseCase.kt
│
├── ui/                       # UI层
│   ├── theme/               # 主题
│   │   ├── Color.kt
│   │   ├── Theme.kt
│   │   └── Type.kt
│   ├── components/          # 可复用组件
│   │   ├── ArticleItem.kt
│   │   ├── Heatmap.kt
│   │   └── ...
│   ├── screens/             # 页面
│   │   ├── home/            # 首页
│   │   │   ├── HomeScreen.kt
│   │   │   └── HomeViewModel.kt
│   │   ├── reader/          # 阅读器
│   │   ├── articles/        # 文章管理
│   │   ├── stats/           # 统计
│   │   └── settings/        # 设置
│   └── navigation/          # 导航
│       └── AppNavigation.kt
│
├── di/                       # 依赖注入
│   └── AppModule.kt
│
└── MainActivity.kt
```

---

## 数据库设计

### Room 实体定义

#### 1. Content（文章内容）

```kotlin
@Entity(tableName = "contents")
data class Content(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    val title: String,
    
    val content: String,
    
    val contentHtml: String? = null,
    
    val chineseChars: Int,
    
    val fontFamily: String = "Microsoft YaHei",
    
    val fontSize: Int = 14,
    
    val fontColor: String = "#000000",
    
    val isBold: Boolean = false,
    
    val isReading: Boolean = true,
    
    val createTime: String = LocalDateTime.now().toString()
)
```

#### 2. ContentCheckIn（内容打卡）

```kotlin
@Entity(
    tableName = "content_checkin",
    indices = [
        Index(value = ["contentId", "date"], unique = true)
    ]
)
data class ContentCheckIn(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    
    val contentId: Long,
    
    val date: String  // YYYY-MM-DD
)
```

#### 3. Config（配置）

```kotlin
@Entity(tableName = "config")
data class Config(
    @PrimaryKey
    val id: Int = 1,
    
    val dailyMinutes: Int = 20,
    
    val theme: String = "system",
    
    val targetCheckRate: Float = 40.0f,
    
    val windowX: Int = -1,
    val windowY: Int = -1,
    val windowWidth: Int = 900,
    val windowHeight: Int = 700,
    
    val todayTasks: String? = null  // JSON 格式存储任务ID列表
)
```

### DAO 接口

#### ContentDao.kt

```kotlin
@Dao
interface ContentDao {
    @Query("SELECT * FROM contents ORDER BY createTime DESC")
    fun getAllContents(): Flow<List<Content>>
    
    @Query("SELECT * FROM contents WHERE isReading = 1 ORDER BY createTime DESC")
    fun getReadingContents(): Flow<List<Content>>
    
    @Query("SELECT * FROM contents WHERE id = :id")
    suspend fun getContentById(id: Long): Content?
    
    @Insert
    suspend fun insertContent(content: Content): Long
    
    @Update
    suspend fun updateContent(content: Content)
    
    @Delete
    suspend fun deleteContent(content: Content)
}
```

#### ContentCheckInDao.kt

```kotlin
@Dao
interface ContentCheckInDao {
    @Query("SELECT date FROM content_checkin WHERE contentId = :contentId ORDER BY date")
    fun getCheckInsByContent(contentId: Long): Flow<List<String>>
    
    @Query("SELECT * FROM content_checkin WHERE date LIKE :yearPrefix || '%' ORDER BY date")
    suspend fun getCheckInDataByYear(yearPrefix: String): List<ContentCheckIn>
    
    @Insert(onConflict = OnConflictStrategy.IGNORE)
    suspend fun insertCheckIn(checkIn: ContentCheckIn): Long
    
    @Delete
    suspend fun deleteCheckIn(checkIn: ContentCheckIn)
    
    @Query("DELETE FROM content_checkin WHERE contentId = :contentId")
    suspend fun deleteCheckInsByContent(contentId: Long)
}
```

---

## 核心功能实现

### 1. 智能任务推荐算法

#### GetTodayTasksUseCase.kt

```kotlin
class GetTodayTasksUseCase @Inject constructor(
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val configRepository: ConfigRepository
) {
    suspend operator fun invoke(): List<Article> {
        val today = LocalDate.now()
        val config = configRepository.getConfig()
        
        // 1. 获取任务池
        val taskPool = getTaskPool(today, config.targetCheckRate)
        if (taskPool.isEmpty()) return emptyList()
        
        // 2. 从任务池中随机组合
        val targetWords = 250 * config.dailyMinutes
        val maxWords = (targetWords * 1.05).toInt()
        
        val shuffled = taskPool.shuffled()
        val result = mutableListOf<Article>()
        var totalWords = 0
        
        for (article in shuffled) {
            if (totalWords + article.chineseChars <= maxWords) {
                result.add(article)
                totalWords += article.chineseChars
            }
        }
        
        // 3. 如果不够，从任务池外补充
        if (totalWords < targetWords) {
            val allReading = contentRepository.getReadingContents()
            val poolIds = taskPool.map { it.id }.toSet()
            val extraPool = allReading.filter { it.id !in poolIds }.shuffled()
            
            for (article in extraPool) {
                if (totalWords + article.chineseChars <= maxWords) {
                    result.add(article)
                    totalWords += article.chineseChars
                    if (totalWords >= targetWords) break
                }
            }
        }
        
        return result
    }
    
    private suspend fun getTaskPool(today: LocalDate, targetRate: Float): List<Article> {
        val allReading = contentRepository.getReadingContents()
        val taskPool = mutableListOf<Article>()
        
        for (article in allReading) {
            val combinedRate = getCombinedRate(article.id, today)
            val threshold = if (today.dayOfMonth <= 5) {
                max(0.0f, targetRate - 5.0f)
            } else {
                targetRate
            }
            
            if (combinedRate <= threshold) {
                taskPool.add(article)
            }
        }
        
        return taskPool
    }
    
    private suspend fun getCombinedRate(contentId: Long, today: LocalDate): Float {
        val currentMonthRate = getArticleCheckRate(contentId, today.year, today.monthValue)
        
        return if (today.dayOfMonth <= 5) {
            val lastMonth = today.minusMonths(1)
            val lastMonthRate = getArticleCheckRate(contentId, lastMonth.year, lastMonth.monthValue)
            (currentMonthRate + lastMonthRate) / 2
        } else {
            currentMonthRate
        }
    }
    
    private suspend fun getArticleCheckRate(contentId: Long, year: Int, month: Int): Float {
        val checkIns = checkInRepository.getArticleCheckIns(contentId, year, month)
        val daysInMonth = YearMonth.of(year, month).lengthOfMonth()
        
        val today = LocalDate.now()
        val totalDays = if (year == today.year && month == today.monthValue) {
            today.dayOfMonth
        } else {
            daysInMonth
        }
        
        return if (totalDays > 0) checkIns.size.toFloat() / totalDays else 0f
    }
}
```

### 2. 热力图实现

#### Heatmap.kt（Compose 自定义绘制）

```kotlin
@Composable
fun Heatmap(
    year: Int,
    checkInData: Map<String, Int>,  // date -> article count
    modifier: Modifier = Modifier
) {
    val weeks = remember(year) { generateWeeks(year) }
    val maxCount = checkInData.values.maxOrNull() ?: 1
    
    Column(modifier = modifier.padding(16.dp)) {
        Text(
            text = "$year 年阅读热力图",
            style = MaterialTheme.typography.titleMedium,
            modifier = Modifier.padding(bottom = 16.dp)
        )
        
        LazyRow(
            horizontalArrangement = Arrangement.spacedBy(4.dp)
        ) {
            items(weeks) { week ->
                Column(
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    week.days.forEach { day ->
                        val dateStr = day.format(DateTimeFormatter.ISO_LOCAL_DATE)
                        val count = checkInData[dateStr] ?: 0
                        val color = getHeatmapColor(count, maxCount)
                        
                        Box(
                            modifier = Modifier
                                .size(12.dp)
                                .clip(RoundedCornerShape(2.dp))
                                .background(color)
                                .clickable { /* 点击显示详情 */ }
                        )
                    }
                }
            }
        }
        
        // 图例
        Row(
            modifier = Modifier.padding(top = 16.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("少", style = MaterialTheme.typography.bodySmall)
            (0..4).forEach { level ->
                Box(
                    modifier = Modifier
                        .size(12.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(getHeatmapColor(level, 4))
                )
            }
            Text("多", style = MaterialTheme.typography.bodySmall)
        }
    }
}

private fun getHeatmapColor(count: Int, maxCount: Int): Color {
    val level = if (maxCount == 0) 0 else (count * 4 / maxCount).coerceIn(0, 4)
    return when (level) {
        0 -> Color(0xFFEBEDF0)
        1 -> Color(0xFF9BE9A8)
        2 -> Color(0xFF40C463)
        3 -> Color(0xFF30A14E)
        4 -> Color(0xFF216E39)
        else -> Color(0xFF216E39)
    }
}

private data class Week(val days: List<LocalDate>)

private fun generateWeeks(year: Int): List<Week> {
    val firstDay = LocalDate.of(year, 1, 1)
    val lastDay = LocalDate.of(year, 12, 31)
    
    // 调整到周一为一周开始
    val startDay = firstDay.minusDays(firstDay.dayOfWeek.value.toLong() - 1)
    
    val weeks = mutableListOf<Week>()
    var currentDay = startDay
    
    while (currentDay <= lastDay) {
        val days = (0..6).map { currentDay.plusDays(it.toLong()) }
        weeks.add(Week(days))
        currentDay = currentDay.plusWeeks(1)
    }
    
    return weeks
}
```

### 3. 文章阅读器

#### ReaderScreen.kt

```kotlin
@Composable
fun ReaderScreen(
    article: Article,
    onCheckIn: () -> Unit,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    var isCheckedIn by remember { mutableStateOf(false) }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(article.title) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "返回")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            Text(
                text = article.content,
                fontSize = article.fontSize.sp,
                fontFamily = when (article.fontFamily) {
                    "serif" -> FontFamily.Serif
                    "monospace" -> FontFamily.Monospace
                    else -> FontFamily.Default
                },
                fontWeight = if (article.isBold) FontWeight.Bold else FontWeight.Normal,
                color = Color(android.graphics.Color.parseColor(article.fontColor)),
                lineHeight = (article.fontSize * 1.5).sp
            )
            
            Spacer(modifier = Modifier.height(32.dp))
            
            Button(
                onClick = {
                    onCheckIn()
                    isCheckedIn = true
                    Toast.makeText(context, "打卡成功！", Toast.LENGTH_SHORT).show()
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = !isCheckedIn
            ) {
                Text(if (isCheckedIn) "已打卡" else "完成阅读并打卡")
            }
        }
    }
}
```

---

## 云同步集成

### 微信云开发 HTTP API

#### CloudApi.kt

```kotlin
interface CloudApi {
    @POST("database/add")
    suspend fun addArticle(
        @Header("X-WX-ENV-ID") envId: String,
        @Header("Authorization") accessToken: String,
        @Body article: CloudArticle
    ): Response<CloudResponse<String>>
    
    @POST("database/query")
    suspend fun getArticles(
        @Header("X-WX-ENV-ID") envId: String,
        @Header("Authorization") accessToken: String,
        @Body query: QueryRequest
    ): Response<CloudResponse<List<CloudArticle>>>
    
    @POST("database/add")
    suspend fun addReadingRecord(
        @Header("X-WX-ENV-ID") envId: String,
        @Header("Authorization") accessToken: String,
        @Body record: CloudReadingRecord
    ): Response<CloudResponse<String>>
    
    @POST("database/query")
    suspend fun getReadingRecords(
        @Header("X-WX-ENV-ID") envId: String,
        @Header("Authorization") accessToken: String,
        @Body query: QueryRequest
    ): Response<CloudResponse<List<CloudReadingRecord>>>
}

data class CloudArticle(
    val title: String,
    val content: String,
    val contentHtml: String?,
    val category: String = "未分类",
    val wordCount: Int,
    val completed: Boolean = false,
    val readProgress: Int = 0,
    val isDeleted: Boolean = false,
    val createdAt: String,
    val updatedAt: String
)

data class CloudReadingRecord(
    val date: String,
    val wordCount: Int,
    val completed: Boolean,
    val timestamp: String
)

data class QueryRequest(
    val collection: String,
    val query: String
)

data class CloudResponse<T>(
    val errcode: Int,
    val errmsg: String,
    val data: T?
)
```

### 数据同步 UseCase

#### SyncDataUseCase.kt

```kotlin
class SyncDataUseCase @Inject constructor(
    private val cloudApi: CloudApi,
    private val contentRepository: ContentRepository,
    private val checkInRepository: CheckInRepository,
    private val configRepository: ConfigRepository
) {
    sealed class Result {
        object Success : Result()
        data class Error(val message: String) : Result()
    }
    
    suspend operator fun invoke(): Result {
        val config = configRepository.getConfig()
        if (!config.cloudEnabled || config.cloudEnvId.isBlank() || config.cloudAccessToken.isBlank()) {
            return Result.Error("云同步未配置")
        }
        
        return try {
            // 1. 上传本地数据到云端
            val localArticles = contentRepository.getAllContentsOnce()
            val localRecords = checkInRepository.getAllCheckInRecords()
            
            localArticles.forEach { article ->
                cloudApi.addArticle(
                    envId = config.cloudEnvId,
                    accessToken = config.cloudAccessToken,
                    article = article.toCloudArticle()
                )
            }
            
            // 2. 从云端获取新数据
            // ... 实现从云端拉取并合并到本地的逻辑
            
            Result.Success
        } catch (e: Exception) {
            Result.Error(e.message ?: "同步失败")
        }
    }
}

private fun Content.toCloudArticle(): CloudArticle {
    return CloudArticle(
        title = title,
        content = content,
        contentHtml = contentHtml,
        wordCount = chineseChars,
        createdAt = createTime,
        updatedAt = LocalDateTime.now().toString()
    )
}
```

---

## UI设计规范

### 主题色

#### 浅色主题

```kotlin
private val LightColors = lightColorScheme(
    primary = Color(0xFF0078D4),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE6F4FF),
    onPrimaryContainer = Color(0xFF004B8D),
    secondary = Color(0xFF40C463),
    onSecondary = Color.White,
    background = Color.White,
    onBackground = Color(0xFF1A1A1A),
    surface = Color(0xFFF5F7FA),
    onSurface = Color(0xFF1A1A1A),
    error = Color(0xFFD13438),
)
```

#### 暗色主题

```kotlin
private val DarkColors = darkColorScheme(
    primary = Color(0xFF60CDFF),
    onPrimary = Color(0xFF00325B),
    primaryContainer = Color(0xFF004B8D),
    onPrimaryContainer = Color(0xFFE6F4FF),
    secondary = Color(0xFF9BE9A8),
    onSecondary = Color(0xFF003918),
    background = Color(0xFF1A1A1A),
    onBackground = Color(0xFFE6E6E6),
    surface = Color(0xFF2B2B2C),
    onSurface = Color(0xFFE6E6E6),
    error = Color(0xFFFF8389),
)
```

### 页面导航图

```
AppNavigation
├─ Home (首页)
│  ├─ 今日任务列表
│  ├─ 热力图
│  └─ 操作按钮（添加/管理/统计/设置）
├─ Reader (阅读器)
├─ Articles (文章管理)
│  ├─ 文章列表
│  └─ AddArticle (添加/编辑文章)
├─ Stats (统计)
└─ Settings (设置)
```

---

## 开发步骤详解

### 第一步：项目初始化

1. **创建新项目**
   - Android Studio → New Project → Empty Compose Activity
   - 语言：Kotlin
   - 最低 SDK：API 26 (Android 8.0)

2. **添加依赖**（build.gradle.kts）

```kotlin
dependencies {
    // Compose
    implementation(platform("androidx.compose:compose-bom:2024.02.00"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.ui:ui-tooling-preview")
    implementation("androidx.compose.material3:material3")
    
    // Navigation
    implementation("androidx.navigation:navigation-compose:2.7.6")
    
    // Room
    implementation("androidx.room:room-runtime:2.6.1")
    implementation("androidx.room:room-ktx:2.6.1")
    kapt("androidx.room:room-compiler:2.6.1")
    
    // DataStore
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    
    // ViewModel
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.7.0")
    
    // Hilt
    implementation("com.google.dagger:hilt-android:2.48")
    kapt("com.google.dagger:hilt-android-compiler:2.48")
    implementation("androidx.hilt:hilt-navigation-compose:1.1.0")
    
    // Retrofit
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
}
```

### 第二步：实现数据层

1. 创建 Room 实体类
2. 创建 DAO 接口
3. 创建 AppDatabase
4. 创建 Repository

### 第三步：实现领域层

1. 创建 UseCase 类
2. 实现任务推荐算法
3. 实现热力图数据计算

### 第四步：实现 UI 层

1. 定义主题和颜色
2. 创建导航组件
3. 实现各页面（Home、Reader、Articles、Stats、Settings）
4. 实现可复用组件

### 第五步：集成云同步

1. 实现 Retrofit API 接口
2. 实现数据同步 UseCase
3. 在设置页面添加同步选项

### 第六步：测试和优化

1. 单元测试（UseCase 测试）
2. UI 测试
3. 性能优化（启动速度、内存占用）

---

## Flutter 方案简要点

如果选择 Flutter 方案，以下是关键技术点：

### 项目结构

```
lib/
├── data/
│   ├── database/          # sqflite
│   ├── models/
│   └── repositories/
├── domain/
│   ├── entities/
│   └── usecases/
├── presentation/
│   ├── providers/         # Riverpod
│   ├── screens/
│   └── widgets/
└── main.dart
```

### 本地数据库（sqflite）

```dart
class DatabaseHelper {
  static final DatabaseHelper instance = DatabaseHelper._init();
  static Database? _database;

  DatabaseHelper._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('daily_read.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, filePath);
    return await openDatabase(path, version: 1, onCreate: _createDB);
  }

  Future _createDB(Database db, int version) async {
    // 创建表结构
  }
}
```

### 热力图（CustomPaint）

```dart
class HeatmapPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    // 自定义绘制热力图
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => true;
}
```

---

## 开发资源

### 参考文档
- [Android Developers - Jetpack Compose](https://developer.android.com/jetpack/compose)
- [Android Developers - Room](https://developer.android.com/training/data-storage/room)
- [微信云开发文档](https://developers.weixin.qq.com/miniprogram/dev/wxcloud/basis/getting-started.html)

### 推荐库
- **图表**：Vico（Compose 图表库）
- **日期选择**：Compose Material 3 Date Picker
- **下拉刷新**： accompanist-swiperefresh

---

*本指南提供了 Android 版开发的完整架构和核心代码示例，开发时可根据实际需求进行调整和扩展*
