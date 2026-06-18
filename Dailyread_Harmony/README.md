# DailyRead · 每日阅读（鸿蒙端）

> 基于 HarmonyOS ArkTS 开发的每日阅读应用，支持文章阅读、背概念、背穴位、背临床、WebDAV 云同步等功能。
> 配套 Windows 端的文章&概念管理器：https://github.com/somnuskwelaweiwei1989/article-concept-manager

---

## 📖 项目简介

DailyRead 是一款面向日常阅读习惯养成的应用，用户可以：

- 📚 添加并阅读文章，支持图片上传（WebP 压缩），每日自动生成今日阅读任务
- 🧠 管理和背诵概念数据（可按分类、学科、章节筛选）
- 📍 背诵人体穴位数据（内置常用穴位库）
- 🏥 管理和背诵**临床笔记**（新增）
- ☁️ 通过 WebDAV 协议与 Windows 端/其他设备同步数据（支持坚果云等主流 WebDAV 服务）
- 💾 本地 JSON 导入/导出数据

---

## 🏗 技术栈

| 技术 | 版本/说明 |
|------|----------|
| 开发平台 | HarmonyOS / OpenHarmony |
| 开发语言 | ArkTS (TypeScript 超集) |
| UI 框架 | ArkUI（声明式开发范式） |
| 数据库 | SQLite（ArkTS 关系型数据 RdbStore API，启用 WAL 模式） |
| 图片处理 | `@ohos.imaging`（ImagePacker）→ WebP 编码 + 自适应压缩 |
| 网络协议 | WebDAV (HTTP/HTTPS) |
| 构建工具 | DevEco Studio + hvigor |

---

## 📂 目录结构

```
DailyRead_Harmony/
├── entry/                          # 主模块
│   └── src/main/ets/
│       ├── entryability/           # 应用入口能力
│       │   ├── EntryAbility.ets
│       │   └── EntryBackupAbility.ets
│       ├── pages/                  # 页面
│       │   ├── SplashPage.ets      # 启动页
│       │   ├── Index.ets           # 路由分发
│       │   ├── Home.ets            # 首页 - 今日阅读
│       │   ├── Reader.ets          # 文章阅读页（支持 WebP 图片显示）
│       │   ├── ArticleManage.ets   # 文章管理（支持图片上传）
│       │   ├── RandomRead.ets      # 随心阅读
│       │   ├── ConceptStudy.ets    # 背概念
│       │   ├── ConceptSettings.ets # 概念管理
│       │   ├── AcupointStudy.ets   # 背穴位
│       │   ├── ClinicalStudy.ets   # 背临床（新增）
│       │   ├── ClinicalSettings.ets # 临床笔记管理（新增）
│       │   └── Settings.ets        # 设置页（含 WebDAV 配置与备份）
│       ├── model/                  # 数据模型
│       │   ├── Article.ets         # 文章（含 imagewebp 字段）
│       │   ├── Concept.ets         # 概念
│       │   ├── ClinicalNote.ets    # 临床笔记（新增）
│       │   ├── Acupoint.ets        # 穴位
│       │   ├── Config.ets          # 应用配置
│       │   ├── CheckInRecord.ets   # 打卡记录
│       │   ├── BuiltInAcupoint.ets # 内置穴位
│       │   ├── RawAcupoint.ets     # 原始穴位数据
│       │   └── PickResult.ets      # 抽取结果
│       ├── repository/             # 数据访问层
│       │   ├── ArticleRepository.ets
│       │   ├── ConceptRepository.ets
│       │   ├── ClinicalNoteRepository.ets（新增）
│       │   ├── AcupointRepository.ets
│       │   ├── ConfigRepository.ets
│       │   ├── CheckInRepository.ets
│       │   ├── DailyTaskRepository.ets
│       │   └── BuiltInAcupointStore.ets
│       ├── service/                # 业务服务层
│       │   ├── DailyTaskService.ets   # 今日任务生成逻辑
│       │   ├── BackupService.ets      # JSON 导入/导出（含临床笔记）
│       │   ├── ImageCompressionService.ets # 图片→WebP 压缩（新增）
│       │   ├── WebDavSyncService.ets  # WebDAV 同步（含临床笔记）
│       │   └── WebDavClient.ets       # WebDAV HTTP 客户端
│       └── database/
│           └── AppDatabase.ets      # 数据库初始化、表结构、升级逻辑（v1~v18）
├── entry/src/main/resources/        # 资源文件（图片、字符串、颜色）
│   └── rawfile/                     # 原始资源（acupoints.json 内置穴位）
├── AppScope/                        # 应用级配置
│   └── resources/base/media/logo.png  # 应用图标
├── build-profile.json5
├── hvigorfile.ts
├── oh-package.json5
└── daily_read_backup_windows.json   # Windows 端备份示例
```

---

## 💾 数据模型与字段说明

### Article（文章）

定义于 [entry/src/main/ets/model/Article.ets](entry/src/main/ets/model/Article.ets)

| 字段 | 类型 | 含义 |
|------|------|------|
| id | number | 主键，自增 |
| title | string | 标题 |
| content | string | 正文 |
| contentHtml | string \| null | HTML 格式内容（可选） |
| chineseChars | number | 汉字字数统计 |
| fontFamily | string | 字体 |
| fontSize | number | 字号 |
| fontColor | string | 字体颜色（#RRGGBB） |
| isBold | boolean | 是否加粗 |
| **isReading** | boolean | 阅读中开关（决定是否进入任务池） |
| **isRequired** | boolean | 必读文章（会被排到今日任务最前面） |
| requiredDays | string | 必读书日期配置（保留字段） |
| useIndependentCheckRate | boolean | 是否使用独立目标打卡率 |
| independentCheckRate | number | 独立目标完成率（0~100） |
| createTime | string | 创建时间（ISO 8601） |
| isLongArticle | boolean | 是否长文章标记 |
| checkInDays | number | 累计打卡天数 |
| completionRate | number | 当前完成率（0~100） |
| **imagewebp** | string | 文章图片（WebP 格式的 base64 字符串，无前缀） |
| lastModified | string | 最后修改时间 |

### ClinicalNote（临床笔记）

定义于 [entry/src/main/ets/model/ClinicalNote.ets](entry/src/main/ets/model/ClinicalNote.ets)

| 字段 | 类型 | 含义 |
|------|------|------|
| id | number | 主键，自增 |
| title | string | 临床笔记标题（如"感冒风寒束表证"） |
| pathogenesis | string | 病机（病因病机分析） |
| treatment | string | 治法（如"辛温解表，宣肺散寒"） |
| prescription | string | 处方（方剂组成与用药） |
| notes | string | 备注（心得体会、注意事项等） |
| isReading | boolean | 学习状态（true=在学习中 / false=已掌握或未开始） |
| createTime | string | 创建时间（ISO 8601） |
| lastModified | string | 最后修改时间 |

> **设计要点**：病机 / 治法 / 处方 / 备注四个字段结构清晰，与中医临床笔记的常用分类完全对应，同时支持标题去重和 lastModified 时间戳做版本合并。

### Concept（概念）

定义于 [entry/src/main/ets/model/Concept.ets](entry/src/main/ets/model/Concept.ets)

| 字段 | 类型 | 含义 |
|------|------|------|
| id | number | 主键 |
| title | string | 概念标题 |
| category | string | 分类 |
| subject | string | 学科 |
| chapter | string | 章节 |
| content | string | 概念内容 |
| isReading | boolean | 背诵开关 |
| createTime | string | 创建时间 |
| lastModified | string | 最后修改时间 |

### Config（应用配置）

定义于 [entry/src/main/ets/model/Config.ets](entry/src/main/ets/model/Config.ets)

| 字段 | 含义 | 默认值 |
|------|------|--------|
| dailyMinutes | 每日目标阅读分钟数 | 20 |
| targetCheckRate | 目标打卡率（0~100） | 30 |
| keepScreenOn | 是否保持屏幕常亮 | false |
| autoSyncWebDav | 是否自动同步 | false |
| autoSyncEnabled | 自动同步总开关 | false |
| webdavUrl / webdavUsername / webdavPassword | WebDAV 连接信息 | 空 |
| webdavRemotePath | WebDAV 远端路径 | /DailyRead |
| lastSyncTime | 上次同步时间 | 空 |
| yesterdayLongArticleIds | 昨日长文章 ID 列表（防重复） | 空 |
| syncArticlesEnabled | 是否同步文章数据 | true |
| syncConceptsEnabled | 是否同步概念数据 | true |
| **syncClinicalNotesEnabled** | 是否同步临床笔记数据 | true |
| lastResetMonth | 上次重置月份（跨月重置打卡） | 空 |

---

## 🖼 核心功能：文章图片上传与 WebP 压缩

### 架构概览

```
用户选择图片（Picker）
      ↓
ImageCompressionService.pickAndCompressToWebP()
      ↓ （解码 → 降尺寸 → WebP 编码 → 循环降质）
返回 base64 字符串（无前缀）
      ↓
写入 Article.imagewebp 字段 → 持久化
      ↓
Reader 页面检测 imagewebp → 渲染 Image('data:image/webp;base64,' + imagewebp)
```

### 压缩策略（核心参数）

核心代码位于 [ImageCompressionService.ets](entry/src/main/ets/service/ImageCompressionService.ets)：

| 参数 | 值 | 说明 |
|------|-----|------|
| 输出格式 | `image/webp` | WebP 有损压缩，体积比 PNG/JPEG 小 ~30%+ |
| 初始 quality | 50 | 中等质量与体积的平衡点 |
| 最大尺寸 | 480px | 宽高任意边超过 480px 时等比缩小（避免大尺寸文章图浪费空间） |
| 体积上限 | 25 KB | 超过上限循环降低 quality（每次 -10，下限 5），最后若仍超限则截断提示 |
| 循环降级 | 最多 10 轮 | quality 50→40→30→…，每轮重新压缩 |
| 读取方式 | PixelMap → ImagePacker.packToBuffer → ArrayBuffer → base64 | 所有操作在内存完成，不写临时文件 |

### base64 格式约定

**重要**：数据库中 `imagewebp` 字段存储的是**纯 base64 字符串，不含 `data:image/webp;base64,` 前缀**。前缀仅在渲染时由 UI 组件拼接。

| 位置 | 格式 |
|------|------|
| 数据库 `imagewebp` | 纯 base64（如 `"UklGRl...AAA="`） |
| JSON 导入/导出 | 同上（直接字符串写入 JSON） |
| WebDAV 上传/下载 | 同上 |
| Image 组件渲染 | `'data:image/webp;base64,' + imagewebp` |

这样约定的好处：
- 与 HarmonyOS `Image('data:image/webp;base64,...')` 原生支持格式完全兼容
- 纯 base64 存储，去掉重复前缀节省磁盘/网络空间
- 跨端一致（鸿蒙端 ↔ Windows 端互导无需转换）

### WebP 解码 / 渲染流程

1. Reader 页读取 `article.imagewebp`
2. 若非空，拼接 `'data:image/webp;base64,' + article.imagewebp`
3. 传给 `Image()` 组件，宽 100%、按原图比例自适应高度（`aspectRatio`）
4. 组件为空则跳过渲染

---

## 🏥 核心功能：临床笔记（Clinical Notes）

### 数据结构

```typescript
export class ClinicalNote {
  id: number = 0;                    // 主键，自增
  title: string = '';                // 标题（如"感冒"、"高血压"）
  pathogenesis: string = '';         // 病机
  treatment: string = '';            // 治法
  prescription: string = '';         // 处方
  notes: string = '';                // 备注
  isReading: boolean = false;        // 学习状态
  createTime: string = '';           // ISO 8601
  lastModified: string = '';         // ISO 8601
}
```

### 数据库表

位于 [AppDatabase.ets](entry/src/main/ets/database/AppDatabase.ets)：

```sql
CREATE TABLE IF NOT EXISTS clinical_notes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT DEFAULT '',
  pathogenesis TEXT DEFAULT '',
  treatment TEXT DEFAULT '',
  prescription TEXT DEFAULT '',
  notes TEXT DEFAULT '',
  isReading INTEGER DEFAULT 0,
  createTime TEXT DEFAULT '',
  lastModified TEXT DEFAULT ''
)
```

### 页面布局

| 页面 | 路径 | 说明 |
|------|------|------|
| **背临床主页面** | [ClinicalStudy.ets](entry/src/main/ets/pages/ClinicalStudy.ets) | 从 `isReading=true` 的临床笔记中随机抽取，格式为 **标签 + 数据**，标签使用红色，顶部对齐 |
| **背临床设置页** | [ClinicalSettings.ets](entry/src/main/ets/pages/ClinicalSettings.ets) | 标题关键字搜索、添加/编辑/删除、学习状态切换；列表只显示标题 |
| **路由** | [main_pages.json](entry/src/main/resources/base/profile/main_pages.json) | 注册 `pages/ClinicalSettings` |

---

## ☁️ WebDAV 同步

### 远端文件

- **文件路径**：`DailyRead/daily_read_backup_windows.json`
- **文件名**：`daily_read_backup_windows.json`
- **HTTP 方法**：上传用 `PUT`，下载用 `GET`，测试连通用 `PROPFIND`
- **认证**：HTTP Basic Auth（Base64(username:password)）

### 上传（syncToRemote）

```
ClinicalNoteRepository.getAllNotes()
  → 遍历 → SyncClinicalNoteData[]
  → JSON.stringify() →  PUT 到 WebDAV 服务器
```

上传时按 `config.syncArticlesEnabled` / `config.syncConceptsEnabled` / `config.syncClinicalNotesEnabled` 三个开关独立控制。

### 下载（syncFromRemote）

```
GET DailyRead/daily_read_backup_windows.json
  → JSON.parse() → SyncPayload
  → 分别解析 articles / concepts / clinicalNotes 数组
  → mergeArticles() / mergeConcepts() / mergeClinicalNotes()
```

### JSON 数据格式（WebDAV + 导入/导出通用）

```json
{
  "version": 6,
  "exportTime": "2026-06-17T10:00:00.000Z",
  "dataType": "daily_read_backup",
  "articles": [
    {
      "id": 1,
      "title": "文章标题",
      "content": "正文内容...",
      "contentHtml": "",
      "chineseChars": 1234,
      "fontFamily": "default",
      "fontSize": 16,
      "fontColor": "#000000",
      "isBold": false,
      "isReading": true,
      "isRequired": true,
      "requiredDays": "",
      "useIndependentCheckRate": false,
      "independentCheckRate": 0,
      "isLongArticle": false,
      "checkInDays": 0,
      "completionRate": 0,
      "imagewebp": "UklGRt...(纯base64，无data前缀)...AAA=",
      "createTime": "2026-06-17T10:00:00.000Z",
      "lastModified": "2026-06-17T10:00:00.000Z"
    }
  ],
  "concepts": [
    {
      "id": 1,
      "title": "概念标题",
      "category": "分类",
      "subject": "学科",
      "chapter": "章节",
      "content": "内容...",
      "isReading": true,
      "createTime": "2026-06-17T10:00:00.000Z",
      "lastModified": "2026-06-17T10:00:00.000Z"
    }
  ],
  "clinicalNotes": [
    {
      "id": 1,
      "title": "感冒·风寒束表证",
      "pathogenesis": "风寒之邪外束肌表，卫阳被遏...",
      "treatment": "辛温解表，宣肺散寒",
      "prescription": "麻黄汤：麻黄 9g、桂枝 6g、杏仁 9g、甘草 3g",
      "notes": "表虚自汗者禁用麻黄汤...",
      "isReading": true,
      "createTime": "2026-06-17T10:00:00.000Z",
      "lastModified": "2026-06-17T10:00:00.000Z"
    }
  ]
}
```

### 合并策略（mergeArticles / mergeConcepts / mergeClinicalNotes）

三种数据类型使用完全一致的合并策略：

| 场景 | 处理 |
|------|------|
| 远端有，本地无 | 插入 |
| 两边都有（按 title 匹配） | 比较 `lastModified`，**远端更新则覆盖** |
| 本地有，远端无 | **保留不动**（不删除本地数据，安全优先） |

### 导入（importFromJSON）

```typescript
// 清空再导入
BackupService.importFromJSON(jsonString, true)

// 按标题去重合并（保留已有数据）
BackupService.importFromJSON(jsonString, false)
```

- **向后兼容**：旧版本 JSON（缺少 `imagewebp`、`clinicalNotes` 等字段）不会报错，自动填充默认值
- **多种键名识别**：`articles` / `articleList` / `contents`、`concepts` / `gainian`、`clinicalNotes` / `notes` / `linchuang` 都能识别
- **标题去重**：以 `title` 为唯一键，跳过已存在项（`clearBeforeImport=false` 时）

### 导出（exportToJSON）

```typescript
const json = await BackupService.exportToJSON()
```

- 导出 **文章 / 概念 / 临床笔记** 全部数据，完整保留所有字段（包括 `imagewebp`）
- 导出版本号：`6`
- dataType：`daily_read_backup`

---

## 🧠 核心业务逻辑：今日任务生成

核心逻辑位于 [DailyTaskService.ets](entry/src/main/ets/service/DailyTaskService.ets) 的 `getOrGenerateTodayTasks()` 方法。

### 算法流程

```
1. 命中缓存？若当日 tasks 已存在 → 直接返回（稳定不变）
2. 从 Config 读取 dailyMinutes 和 targetCheckRate
3. 任务池筛选：isReading=true 且 completionRate < effectiveRate
   （effectiveRate：有独立目标率优先用它，否则用全局 targetCheckRate）
4. 必读前置：将 isRequired=true 的文章先排到结果最前面
5. 计算字数上限：maxWordLimit = dailyMinutes × 250 × (1.01~1.11 随机系数)
6. 长/短文章分类：字数 > maxWordLimit × 30% 判定为长文章
7. 分支选取：
   A) 无长文章 → 用短文章随机填满字数上限
   B) 1 篇长文章 → 若它本身 ≤ maxWordLimit 必选，剩余用短文章补
   C) ≥2 篇长文章 → 随机组合长文章（总字数 ≤ maxWordLimit×70%），
      防重复校验：昨日长文章列表作为「黑名单参考」，剩余用短文章补
8. 转换为 DailyTaskItem 列表，持久化到 daily_tasks 表
```

### 防重复机制

- 短文章选取：最多 100 次随机抽取，每次从候选池移除已选项
- 长文章选取：通过 `yesterdayLongArticleIds` 对比昨日与今日列表，最多 10 次尝试避免相同组合
- 若多次尝试仍无法避免重复 → 降级允许重复

---

## 🛠 构建与运行

### 环境要求

- **DevEco Studio**（推荐 5.0+）
- HarmonyOS SDK（API 11+）
- Node.js 16+（hvigor 构建工具依赖）

### 构建步骤

1. 用 DevEco Studio 打开本项目
2. 依赖自动同步（oh-package）
3. 连接真机或启动模拟器
4. 点击运行按钮（▶）构建并安装 hap

### 命令行构建

```bash
# 构建
hvigorw assembleHap

# 清理
hvigorw clean
```

---

## 🗄 数据库设计

位于 [AppDatabase.ets](entry/src/main/ets/database/AppDatabase.ets)

| 表名 | 说明 |
|------|------|
| contents | 文章表 |
| concepts | 概念表 |
| **clinical_notes** | 临床笔记表（v15 新增） |
| acupoints | 穴位表 |
| content_checkins | 打卡记录表 |
| config | 应用配置（单条） |
| daily_tasks | 每日任务（日期维度） |
| daily_task_items | 每日任务条目（文章维度，关联 daily_tasks） |

### 设计要点

- **主键自增**：所有表使用 `INTEGER PRIMARY KEY AUTOINCREMENT`
- **WAL 模式**：`PRAGMA journal_mode=WAL` + `synchronous=FULL` 保证写入持久化，避免数据丢失
- **字段缺失即降级**：导入/下载时，每个字段使用 `|| 默认值` 方式容错，能兼容旧版 JSON 备份
- **自动升级**：`init()` 中按需要执行 ALTER TABLE，保证版本兼容；不会 DROP TABLE
- **版本号**：当前 DB_VERSION = 18

### 数据库版本升级历史

| 版本 | 变更 |
|------|------|
| v10 → v11 | articles 表加 `completionRate REAL DEFAULT 0` |
| v11 → v12 | articles 表加 `checkInDays INTEGER DEFAULT 0` |
| v13 → v14 | config 表加 `lastResetMonth TEXT DEFAULT ''` |
| v14 → v15 | 新增 `clinical_notes` 表、`daily_tasks` 表、`daily_task_items` 表 |
| v15 → v17 | articles 表加 `imagewebp TEXT DEFAULT ''` |
| v17 → v18 | config 表加 `syncClinicalNotesEnabled INTEGER DEFAULT 1` |

---

## 📱 页面导航

```
首页 (Home)
  ├─ 今日目标（字数、目标率、完成数/总数）
  ├─ 今日任务列表（文章 + 必读标记 + ✓ 打卡完成状态）
  │   ├─ "📖 随机阅读"按钮 → 从**未完成文章**中随机抽取一篇进入阅读页
  │   └─ 点击文章 → 阅读页 (Reader)
  └─ 底栏：首页 · **背临床** · 随心阅读 · 背穴位 · 背概念 · 设置

背临床 (ClinicalStudy)                 ← v1.6.0 新增
  └─ 随机展示 isReading=true 的临床笔记，"下一个"切换
     （标签 + 数据，红色标签左对齐，顶部起排）

背临床设置 (ClinicalSettings)          ← v1.6.0 新增
  ├─ 新增临床笔记（标题、病机、治法、处方、备注、学习状态复选框）
  ├─ 编辑 / 删除 / 切换学习状态
  └─ 关键字筛选（只显示标题）

文章管理 (ArticleManage)
  ├─ 新增文章（标题、内容、阅读中、必读复选框、图片上传）
  ├─ 编辑文章（含 WebP 图片预览与替换）
  ├─ 多选批量删除
  └─ 独立目标率设置

概念设置 (ConceptSettings)
  ├─ 新增概念（标题、分类、学科、章节、内容）
  ├─ 编辑 / 删除
  └─ 关键字筛选

背概念 (ConceptStudy)
  └─ 随机展示 isReading=true 的概念数据，"下一个"切换

背穴位 (AcupointStudy)
  └─ 基于内置 acupoints.json 穴位库随机抽取

设置 (Settings)
  ├─ 每日阅读时间
  ├─ 目标打卡率
  ├─ 阅读设置 → 文章管理入口
  ├─ 同步开关（文章 / 概念 / 临床笔记 独立）
  ├─ 坚果云 WebDAV 同步配置指引
  ├─ 测试 WebDAV 连接
  ├─ 上传 / 下载
  └─ 本地 JSON 导入 / 导出
```

---

## ✅ 必读标记机制

- **开关位置**：`ArticleManage.ets` 添加/编辑文章弹窗中，"必读"复选框位于"阅读中"下方
- **列表展示**：文章管理列表中，`isRequired=true` 的文章标题右侧会显示红色五角星 ★
- **任务排序**：`DailyTaskService` 生成今日任务时，必读文章会被优先直接放入任务列表最前端，再进行剩余文章的随机选取

---

## 🔄 备份与导入兼容说明

### 导出

```typescript
BackupService.exportToJSON()
// → version=6, dataType="daily_read_backup"
```
- 导出 **所有字段**（含 imagewebp、isRequired、checkInDays、completionRate 等）
- 同时导出 articles / concepts / **clinicalNotes**

### 导入

```typescript
BackupService.importFromJSON(jsonString, clearBeforeImport)
```

- **完全兼容旧版**：所有新增字段都附带默认值（`imagewebp=""`、`isRequired=false`、`checkInDays=0` 等），旧版 JSON 缺少字段不会报错
- `clearBeforeImport=true` → 先清空再插入
- `clearBeforeImport=false` → 按 `title` 去重合并，跳过已存在项
- 能识别 `articles` / `articleList` / `contents` / `clinicalNotes` / `notes` / `linchuang` 等多种键名

---

## 🔐 权限说明

本应用所使用的权限均声明在 `entry/src/main/module.json5` 的 `requestPermissions` 节点内。

### 清单权限（在 module.json5 中明确声明）

| 权限常量 | 用途说明 | 授权级别 |
|----------|----------|----------|
| `ohos.permission.INTERNET` | 提供 WebDAV 上传/下载、测试连接等网络通信能力 | normal（正常权限，安装时自动授予） |

### 系统默认已开放的能力（无需单独申请）

HarmonyOS 对以下能力在 API 11+ 默认开放，不需要写入 `requestPermissions`：

- **应用内文件读写**（`context.filesDir` / `context.cacheDir`）：用于写入 JSON 导出文件、缓存 WebDAV 下载内容、图片压缩临时文件
- **图片选择**（`@ohos.file.picker`）：用于选择图片上传到文章
- **窗口常亮**（`Window.setWindowKeepScreenOn`）：由 Config 中的 `keepScreenOn` 控制
- **关系型数据库（RdbStore）**：SQLite 数据库创建与读写

> 💡 如果需要把导出文件放到外部存储供用户手动查看（如"文档"目录），或访问 `pictures` 等系统相册，
> 则需要额外声明 `ohos.permission.READ_IMAGEVIDEO` / `ohos.permission.READ_PASTEBOARD`
> 以及 `ohos.permission.WRITE_IMAGEVIDEO` 并在运行时调用 `requestPermissionsFromUser` 申请用户授权。
> 当前 DailyRead 的导入/导出功能均走应用私有沙箱路径，不触发用户授权弹窗。

### 权限申请流程

应用未做运行时权限申请（Runtime Permission）逻辑，所有网络能力依赖安装时自动授予的 `ohos.permission.INTERNET`。
首次启动时仅进行数据库初始化与 WebDavSyncService 上下文注入（`EntryAbility.ets`）。

---

## 🆙 版本更新日志

### v1.6.0 — 2026-06-17

**✨ 新功能：文章图片上传（WebP 压缩）+ 阅读页按原图比例自适应显示**

- **数据模型**：`Article` 模型新增 `imagewebp: string` 字段（存储 WebP 格式的 base64 字符串）
- **数据库**：v16 → v17 升级脚本 `ALTER TABLE articles ADD COLUMN imagewebp TEXT DEFAULT ''`
- **图片压缩服务**（[ImageCompressionService.ets](entry/src/main/ets/service/ImageCompressionService.ets)）**【核心】**：
  - 调用 `@ohos.file.picker.PhotoViewPicker` 让用户选择图片
  - 解码为 `PixelMap` → 等比缩放到最大 480px（保持宽高比）
  - 使用 `ImagePacker` 重新编码为 **WebP**，初始 `quality=50`
  - 若体积 > **25KB** → 循环降低 quality（每次 -10，下限 5），每轮重新编码
  - 最终将 ArrayBuffer 转 base64 返回
  - 同时提供 `base64ToPixelMap()` 方法，供预览和阅读页使用（含原图宽高比）
  - 提供 `SizedPixelMap` 接口，返回 `{ pixelMap, width, height }` 三元组
- **文章添加/编辑**（[ArticleManage.ets](entry/src/main/ets/pages/ArticleManage.ets)）：
  - 新增"上传图片"卡片区域，含图标 + 描述 + 选择按钮
  - 选择后预览已选图片，显示尺寸信息
  - 空时支持占位图，有图时支持点击替换
  - 编辑页加载时自动解码已有 imagewebp 供预览
- **阅读页显示**（[Reader.ets](entry/src/main/ets/pages/Reader.ets)）**【核心】**：
  - 正文检测 `article.imagewebp` 非空 → 渲染 `Image('data:image/webp;base64,' + imagewebp)`
  - 使用 `aspectRatio(原图宽/原图高)` 让图片**宽度自适应容器，高度按原图比例缩放**
  - 顶部对齐，左对齐，不固定高度（解决此前图片被挤压显示问题）
- **同步兼容**：
  - 本地导入/导出（[BackupService.ets](entry/src/main/ets/service/BackupService.ets)）：`BackupArticleData` 含 `imagewebp`
  - WebDAV 同步（[WebDavSyncService.ets](entry/src/main/ets/service/WebDavSyncService.ets)）：`SyncArticleData` 含 `imagewebp`，上传/下载/合并均完整处理
  - 与 Windows 端 JSON 互导字段对齐（纯 base64，无 data 前缀）

**✨ 新功能：临床笔记（Clinical Notes）完整模块**

- **数据模型**（[ClinicalNote.ets](entry/src/main/ets/model/ClinicalNote.ets)）**【核心】**：9 个字段（title / pathogenesis / treatment / prescription / notes / isReading / id / createTime / lastModified）
- **数据库表**（[AppDatabase.ets](entry/src/main/ets/database/AppDatabase.ets)）：`clinical_notes` 表，所有 TEXT 字段带 DEFAULT ''，`isReading` 使用 INTEGER 存储（0/1）
- **数据访问层**（[ClinicalNoteRepository.ets](entry/src/main/ets/repository/ClinicalNoteRepository.ets)）：
  - `getAllNotes()` — 全量读取
  - `getReadingNotes()` — 仅 isReading=true
  - `insertNote()` / `updateNote()` / `deleteNote()` / `deleteAllNotes()` — CRUD
  - `updateReadingStatus(id, bool)` — 单独切换学习状态
- **背临床主页面**（[ClinicalStudy.ets](entry/src/main/ets/pages/ClinicalStudy.ets)）：
  - 与背概念一致的随机切换逻辑
  - 每个字段显示为 **"标签: 数据"**，标签为红色粗体，数据为普通文字
  - Row 布局：`alignItems(VerticalAlign.Center)`，标签与数据同一水平线
  - 内容 Column 使用 `justifyContent(FlexAlign.Start)` 顶部对齐
- **背临床设置页**（[ClinicalSettings.ets](entry/src/main/ets/pages/ClinicalSettings.ets)）：
  - 与背概念设置一致的列表/编辑布局
  - 列表中只显示笔记标题（病机/治法/处方不显示，避免过长）
  - 编辑对话框含全部 6 个字段的输入 + "学习中"复选框
  - 支持关键字搜索
- **JSON 导入/导出**（[BackupService.ets](entry/src/main/ets/service/BackupService.ets)）：
  - `BackupClinicalNoteData` 完整字段
  - `exportToJSON()` → `clinicalNotes` 数组
  - `importFromJSON()` → 支持 `clinicalNotes` / `clinical_notes` / `notes` / `linchuang` 等多种键名
  - `clearBeforeImport=true` 时清理临床笔记表
  - 去重按 `title` 做唯一键
- **WebDAV 同步**（[WebDavSyncService.ets](entry/src/main/ets/service/WebDavSyncService.ets)）：
  - `SyncClinicalNoteData` 与 ClinicalNote 字段对齐
  - 上传时按 `config.syncClinicalNotesEnabled` 开关决定是否打包
  - 下载时调用 `mergeClinicalNotes()`（策略与 mergeArticles / mergeConcepts 一致）
  - `SyncResult` 新增 `uploadedClinicalNotes` / `downloadedClinicalNotes` 计数
- **应用配置**（[Config.ets](entry/src/main/ets/model/Config.ets)）：
  - 新增 `syncClinicalNotesEnabled: boolean = true`
  - 设置页面增加同步开关卡片（与文章、概念开关并排）
  - 数据库 v17→v18 升级脚本加 `ALTER TABLE config ADD COLUMN syncClinicalNotesEnabled INTEGER DEFAULT 1`

**✨ 导航调整：底栏文章管理 → 背临床；文章管理移至设置页**

- **底栏顺序**（与所有页面保持一致）：首页 · **背临床** · 随心阅读 · 背穴位 · 背概念 · 设置
- 原"文章管理"从底栏移除，改在 `Settings.ets` "阅读设置"标题下新增入口卡片

**版本号**：设置页底部显示 `版本号: 1.6.0`

---

### v1.5.0 — 2026-06-16

**🐛 Bug 修复：今日阅读列表"已完成"状态显示不正确**

- **问题**：在阅读页完成打卡后点击"←"返回首页，首页任务列表仍显示该文章未完成
- **根因**：1. `router.back()` 返回时 Home 页面走缓存恢复，`aboutToAppear()` / `loadData()` 不重新执行；2. `AppStorage` 的 `dataRefreshSignal` 在 Home 页面不可见或监听不生效
- **修复方案**（三层保障）：
  1. **渲染层实时判定**：Home 中 `TaskCard` 的 `isCheckedIn` 改为直接调用同步方法 `isArticleCheckedIn(articleId, item.isCheckedIn)`
  2. **AppStorage 实时同步**：新增 `todayCheckedInIds` 键，格式为 `"2026-06-16|id1,id2,id3"`，Reader 打卡成功后立即写入；Home 用 `@StorageLink` 实时感知并触发重新渲染
  3. **DB 启动同步**：Home `aboutToAppear` 中调用 `syncTodayCheckedInIdsToStorage()`，从 `check_in_records` 表读取今日打卡文章并写入 AppStorage

**✨ 新功能：随机阅读按钮**

- **位置**：首页"今日任务"标题行右侧，📖 图标 + 文字"随机阅读"
- **行为**：从今日任务中 isCheckedIn=false 的文章随机抽取一篇 → 进入阅读页

---

## 🧪 测试

- `entry/src/ohosTest/ets/test/Ability.test.ets`：Ability 启动测试
- `entry/src/ohosTest/ets/test/List.test.ets`：列表组件测试
- `entry/src/test/LocalUnit.test.ets`：本地单元测试

在 DevEco Studio 中选择对应 Test 目录 → 右键 **Run Tests**。

---

## 📝 开发规范

| 项目 | 规范 |
|------|------|
| 代码风格 | 2 空格缩进，严格 ArkTS |
| 命名 | `PascalCase` 用于类与接口；`camelCase` 用于方法与变量 |
| 业务层分层 | page → service → repository → database |
| 数据库写入 | 所有表字段修改必须在 `AppDatabase.init()` 中加入对应的 `ALTER TABLE` 升级语句并 **增加 DB_VERSION** |
| 时间格式 | 统一 ISO 8601（`new Date().toISOString()`） |
| 图片 base64 | 统一 **纯 base64（无前缀）** 存储，渲染时加 `'data:image/webp;base64,'` 前缀 |
| 中文编码 | JSON 解析前做字符容错，避免中文乱码 |

---

## 📄 License

本项目遵循 MIT License。
