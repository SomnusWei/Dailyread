# DailyRead · 每日阅读 + 炎武班学习中心

> 面向日常阅读习惯养成与中医传承教学的跨平台应用套件，包含鸿蒙端 APP、Windows 端管理器、云端同步服务与炎武班学习中心 PWA。

---

## 📖 项目简介

DailyRead 是一套帮助用户养成每日阅读习惯的工具，支持文章阅读、音频朗读、磨耳跟背等学习场景。整个项目由三个子项目组成，覆盖移动端阅读、桌面端管理和云端数据同步。

在 DailyRead 主功能之外，服务端同时托管了**「炎武班学习中心」**——一个面向中医传承教学场景的 PWA 应用，支持讲义分发、作业布置与批改、消息通知等教学全流程，由魏玮教授组建的炎武班团队使用。

### 核心功能

#### DailyRead 阅读套件

- 📚 **文章管理**：文章增删改查、图片上传（WebP 压缩）、批量编辑、表格排序
- 📋 **每日阅读**：每日自动生成阅读任务，打卡记录，完成率统计，支持"待缓再读"跳过当前文章
- 🔊 **音频朗读**：文章支持 m4a 音频，Win 端录入转码（ffmpeg）、鸿蒙端 AVPlayer 自动播放/循环播放、三端同步透传
- 🎧 **磨耳跟背**：鸿蒙端独立底栏入口，只展示有音频的文章，进入简化阅读页专注跟听跟背
- ⚙️ **多端配置同步**：每日阅读时长、目标完成率、自动播放/循环播放等配置双端共享、实时同步（字号为各端本地设置，不同步）
- ☁️ **多端同步**：通过后端 API 实现鸿蒙端与 Windows 端数据实时互通；since 增量游标按 user_id 隔离，切换账号自动重置触发全量拉取
- 💾 **数据备份**：支持 JSON 导入/导出，一键迁移；Win 端额外提供"全量导出（服务器）"按钮，从服务器拉取账号全量数据（文章含音频/图片 base64、打卡记录、用户配置、今日任务）打包备份
- 🟢 **服务器状态监控**：五端（鸿蒙首页/文章管理/磨耳跟背/随心阅读/设置 + Win 端状态栏）实时显示服务器连通状态
- 🌐 **官方网站**：项目官网展示项目介绍、功能特性、技术架构，支持在线注册账号
- 🔐 **管理后台**：管理员登录后台，查看数据统计、用户管理（增删改查）

#### 炎武班学习中心（PWA）

- 🎓 **用户等级体系**：管理员、教师、博士生、研究生、本科生、师承生；管理员/教师为教职工角色（STAFF），其他为学生角色
- 📄 **讲义分发**：教师/管理员上传 HTML 讲义并按学生等级分发；支持 12 个分类筛选（基础学｜诊断学｜针灸腧穴｜中药｜方剂｜内科｜外科｜妇科｜儿科｜推拿｜养生｜经典）；学员点击在线阅读；已分发讲义可**追加分发**（追加等级或指定账号，自动向未收到通知的账号补发通知且去重不重复打扰）；讲义可见性按等级动态匹配，新建账号可查看其等级范围内的历史讲义；「分发讲义」按钮以模态弹窗形式打开（分发表单 + 我的分发记录），不在列表下方展开；**标题留空时自动以上传 HTML 文件名（去扩展名）作为标题**（前端取文件名 + 后端兜底，校验放宽）
- 🔲 **列表/网格视图切换**：讲义库支持列表视图与 4 列网格视图两种显示方式，标题栏右侧视图切换按钮（列表/网格图标），用户选择 localStorage 持久化，窄屏响应式降列（1024px→2 列、640px→1 列）
- 🔐 **删除讲义密码二次确认**：删除讲义需输入登录账号密码，前端弹出确认框（显示当前账号 + 密码输入 + 回车提交），后端 `DELETE /handouts/:id` 路由 bcrypt 校验当前账号密码，密码错误拒绝删除；讲义库列表与「我的分发记录」两处删除入口统一走同一弹窗
- 📝 **作业布置**：富文本编辑器编辑作业，按学生等级分发；支持设置提交时间范围（开始时间/截止时间），超期学员不可再提交，仅可查看作业与评分评语
- 📤 **学员作业提交**：学员在作业区对指定作业上传文件（Word 文档、Excel 表格、PDF 文档、图片），每人每作业一份，重复提交覆盖旧文件并重置成绩；文件大小上限 20MB
- ✅ **教师批改**：作业布置者可查看提交列表，录入分数与评语，批改结果通过收件箱通知学员；支持重新批改
- 📬 **消息通知**：讲义/作业分发、作业批改结果均自动推送到学员收件箱，支持已读/未读筛选与批量已读
- 📊 **阅读完成率**：教师/管理员按等级筛选已绑定 DailyRead 的学员，查看自然周/自然月阅读完成率柱状图；周/月视图**独立选择时间范围**（周视图选任意一天显示该自然周，月视图直接选月份），数据实时来自学员绑定账号的打卡记录（只读查询，不改动 DailyRead 数据表，不影响 Win/鸿蒙端）
- ⏱ **阅读打卡（PWA）**：学习中心内嵌 DailyRead PWA 阅读页新增打卡按钮，进入页面 10 秒后才允许打卡（倒计时提示、防重复打卡），打卡数据写入绑定账号
- 📊 **分发记录**：教师/管理员可在"我的讲义"与"我的作业"面板查看自己的分发记录与学员提交情况
- 📲 **PWA 支持**：通过 manifest.json + Service Worker 支持安装到桌面/离线访问；核心 shell 资源（app.html/app.js/center.css/login.js）网络优先保证版本一致、其它静态资源缓存优先 + 后台更新，API 与上传内容仅网络获取；新 SW 接管时老标签页自动刷新一次，用户侧无感更新

---

## 🏗 技术栈

| 子项目 | 语言/框架 | 说明 |
|--------|-----------|------|
| Dailyread_Harmony | ArkTS / ArkUI | 鸿蒙端移动应用 |
| Dailyread_win_article_concept_manager | Python / PyQt 6 | Windows 桌面管理工具 |
| dailyread-server | Node.js / Express / MySQL | 后端同步服务 + 官网 + 学习中心 PWA |

---

## 📂 目录结构

```
DailyRead/
├── Dailyread_Harmony/                      # 鸿蒙端 APP
│   ├── entry/
│   │   └── src/main/ets/
│   │       ├── pages/                      # 页面（首页、阅读、随心阅读、设置等）
│   │       ├── model/                       # 数据模型（Article/Config/ApiTypes）
│   │       ├── repository/                  # 数据访问层
│   │       ├── service/                     # 业务服务层（含 AudioService 音频播放、ApiClient 含按 user_id 隔离的 since 游标）
│   │       └── database/                   # SQLite 数据库（版本化迁移）
│   └── README.md                           # 鸿蒙端详细文档
│
├── Dailyread_win_article_concept_manager/   # Windows 端管理器
│   ├── article_concept_manager.py          # 主程序（含音频转码、批量导入、服务器状态指示灯、全量导出）
│   ├── api_client.py                       # 后端 API 客户端（登录成功自动重置 since）
│   ├── sync_service.py                     # 同步服务（since 按 user_id 隔离）
│   ├── app.spec                            # PyInstaller 打包配置
│   └── requirements.txt                    # 依赖列表
│
├── dailyread-server/                       # 后端服务 + 官网 + 学习中心 PWA
│   ├── src/
│   │   ├── routes/
│   │   │   ├── articles.js                 # 文章 CRUD + 增量同步
│   │   │   ├── auth.js                     # DailyRead 认证
│   │   │   ├── checkins.js                 # 打卡记录
│   │   │   ├── config.js                   # 用户配置
│   │   │   ├── dailyTasks.js               # 每日任务
│   │   │   ├── admin.js                    # 管理后台
│   │   │   ├── migrate.js                  # 数据迁移
│   │   │   ├── learning.js                 # 炎武班学习中心 API
│   │   │   └── drProxy.js                  # DailyRead PWA 代理路由（/api/dr/* 按 drUserId 转发）
│   ├── cron.js                         # 定时任务（00:00 生成阅读任务 / 12:00 结算完成率）
│   ├── cron/
│   │   └── drSettle.js                 # DailyRead PWA 完成率结算（每天 12:00）
│   ├── middleware/
│   │   ├── auth.js                     # 认证中间件（区分 DailyRead / Learning Center token）
│   │   ├── lcDrProxyAuth.js            # 学习中心 DailyRead 代理鉴权（lc token + 绑定检查 + 注入 drUserId）
│   │   └── errorHandler.js
│   ├── db/
│   │   ├── init.js                     # DailyRead 表初始化与迁移
│   │   └── learning_init.js            # 学习中心表初始化（含 lc_users.dr_user_id 绑定 + lc_dr_completion_rates 完成率）
│   ├── utils/response.js
│   ├── config.js                       # 配置加载
│   ├── db.js                           # 数据库连接池
│   └── index.js                        # 服务入口
│   ├── public/
│   │   ├── index.html                      # 门户首页（DailyRead 介绍 + 炎武班介绍 + 双入口）
│   │   ├── register.html                   # DailyRead 用户注册
│   │   ├── login.html                      # 管理员登录
│   │   ├── admin.html                      # 管理后台（统计 + 用户管理）
│   │   ├── manifest.json                   # PWA 配置
│   │   ├── sw.js                           # Service Worker（缓存版本管理）
│   │   ├── css/style.css                   # 全站样式
│   │   ├── js/                             # 官网交互脚本
│   │   └── center/                         # 炎武班学习中心 PWA
│   │       ├── index.html                  # 学习中心入口（登录态检查）
│   │       ├── app.html                    # 学习中心 SPA 主页
│   │       ├── css/center.css              # 学习中心样式
│   │       ├── js/
│   │       │   ├── login.js                # 学习中心登录
│   │       │   └── app.js                  # SPA 核心逻辑（分类筛选/时间窗/提交/批改）
│   │       ├── icons/                      # PWA 图标
│   │       └── dr/                         # DailyRead PWA 嵌入版
│   │           ├── bind.html               # DailyRead 账号绑定引导页
│   │           ├── app.html                # DailyRead PWA 主应用（代理模式）
│   │           ├── css/dr.css              # DailyRead PWA 样式
│   │           └── js/
│   │               ├── bind.js             # 绑定逻辑（lc token → DailyRead 鉴权 → 写入绑定）
│   │               └── app.js              # PWA 核心逻辑（代理请求注入 req.drUserId）
│   ├── downloads/                          # 可执行下载资源
│   │   └── DailyRead_Win.zip               # Windows 端管理器打包（从 PyInstaller dist 导出）
│   ├── scripts/
│   │   ├── account_manager.py             # 账号管理工具
│   │   ├── delete-user.js                 # 删除用户（含数据级联清理）
│   │   ├── delete-user.sql
│   │   └── clean_backslash_files.py       # 文件路径分隔符修复
│   ├── schema.sql                          # DailyRead 建表脚本
│   ├── check_admin.sql                    # 管理员账号查询
│   ├── dailyread_nginx.conf                # Nginx 配置示例
│   ├── .env.example                        # 环境变量模板
│   └── package.json
│
├── 炎武班介绍.txt                            # 炎武班团队介绍（首页展示文案）
├── 音频功能方案.md                          # 音频全链路设计文档
├── 鸿蒙 (HarmonyOS) Base64 m4a 音频自动播放开发指南.txt
└── .gitignore
```

---

## 🚀 快速开始

### 1. 后端服务（dailyread-server）

```bash
# 安装依赖
cd dailyread-server
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env，设置数据库连接、JWT 密钥等

# 初始化数据库
npm run init-db        # DailyRead 主表
node src/db/learning_init.js   # 炎武班学习中心表

# 启动服务
npm start
```

### 2. Windows 端管理器

```bash
cd Dailyread_win_article_concept_manager

# 安装依赖
pip install -r requirements.txt

# 运行程序
python article_concept_manager.py

# 或打包为 EXE
python -m PyInstaller --clean --noconfirm app.spec
```

### 3. 鸿蒙端 APP

使用 DevEco Studio 打开 `Dailyread_Harmony/` 目录，连接真机或模拟器后直接运行。

详细开发文档见各子目录的 README.md。

### 4. 炎武班学习中心 PWA

服务启动后直接通过浏览器访问 `https://your-domain/center/` 即可使用。首次使用需管理员登录后新建账号并设置等级，再分发给学员。支持安装到桌面（PWA）。

---

## 🎧 音频功能

文章支持音频朗读，全链路如下：

```
Win 端录入            后端存储                鸿蒙端播放
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 选 mp3/wav   │    │ articles.    │    │ 同步拉取     │
│ ffmpeg 转码  │ ─► │ audiobase64  │ ─► │ base64 解码  │
│ → m4a base64 │    │ LONGTEXT     │    │ → AVPlayer   │
└──────────────┘    └──────────────┘    └──────────────┘
```

| 端 | 实现 |
|----|------|
| **Win 端** | ffmpeg 转码为 m4a/AAC-LC，base64 编码写入 `audiobase64`；支持单篇录入、**批量导入**（选文件夹→按标题匹配→进度条转码→自动上传）、**批量修改「是否显示文章内容」开关**（无图文章自动跳过）；保存采用线程锁 + os.replace 原子写 |
| **后端** | `articles` 表 `audiobase64 LONGTEXT` 列，CRUD 透传，`init.js` 自动迁移；每日 00:00 cron 根据 `daily_minutes × 100 字/分钟 × 随机因子(1.01~1.10)` 生成当日任务字数基数 |
| **鸿蒙端** | `AudioService` 清洗→二进制解码→沙箱临时文件→AVPlayer fd 协议→状态机回调 prepare；三阅读页（Reader/RandomRead/EarPracticeReader）控制条；Settings 支持「自动播放」「循环播放」开关 |

**Win 端依赖**：需安装 ffmpeg。通过 winget 安装后 APP 会自动扫描路径作为 fallback。

---

## 🔗 子项目关系

```
┌─────────────────┐     API              ┌─────────────────┐
│  Dailyread_      │ ◄──────────────────► │  dailyread-     │
│  Harmony (手机)  │                      │  server (云端)   │
└────────┬────────┘                      └────────▲────────┘
         │                                        │
         │  JSON 导入/导出                         │ API
         ▼                                        │
┌─────────────────┐                               │
│  Dailyread_win_  │ ◄────────────────────────────┘
│  article_concept │
│  _manager (PC)   │
└─────────────────┘
```

- **鸿蒙端** 与 **Windows 端** 通过 **后端 API** 双向实时同步
- 两端也可独立使用 **JSON 导入/导出** 进行数据迁移
- 后端提供用户体系、数据持久化和增量同步能力
- 同一域名下还托管炎武班学习中心 PWA（独立用户体系，不与 DailyRead 共用账号）

---

## 🗄 数据库设计

### DailyRead 主表

后端使用 MySQL，主要表结构：

| 表名 | 说明 |
|------|------|
| users | 用户表（用户名、密码、角色） |
| articles | 文章表（多端同步字段 `client_id` + `user_id` 唯一；含 `imagewebp` 图片、`audiobase64` 音频、`iscontent` 是否显示内容） |
| checkins | 打卡记录表 |
| daily_tasks | 每日任务表 |
| daily_task_items | 每日任务条目表 |
| user_configs | 用户配置表（`daily_minutes` 每日阅读时长、`target_check_rate` 目标完成率、`reader_font_size` 字号、`auto_play_audio` 自动播放、`loop_audio` 循环播放等） |

### 炎武班学习中心表

学习中心使用独立用户体系，通过 `learning_init.js` 初始化：

| 表名 | 说明 |
|------|------|
| lc_users | 学习中心用户（username/password_hash/nickname/role 等级；新增 `dr_user_id` + `dr_bound_at` 单向绑定 DailyRead 账号） |
| lc_handouts | 讲义（uploader_id/level_scope 分发等级/extra_users 指定账号 JSON 数组/category 分类 12 选 1/html_file 路径） |
| lc_assignments | 作业（uploader_id/levels 分发等级数组/start_at/due_at 时间窗/content 富文本） |
| lc_inbox | 收件箱（receiver_id/sender_id/type 类型/title/body/read 已读） |
| lc_submissions | 学员作业提交（assignment_id/student_id 唯一约束/filename/original_name/file_size/score/comment/graded_at/graded_by） |
| lc_dr_completion_rates | DailyRead PWA 完成率结算（lc_user_id/task_date 唯一约束/completion_rate 百分比/打卡数） |

---

## 📡 API 路由

### DailyRead

| 模块 | 路由前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/auth` | 注册、登录、JWT 签发 |
| 文章 | `/api/articles` | 文章 CRUD、批量同步（`since` 增量游标按 user_id 隔离） |
| 打卡 | `/api/checkins` | 打卡记录管理 |
| 配置 | `/api/config` | 用户配置读写 |
| 每日任务 | `/api/daily-tasks` | 任务生成与同步 |
| 管理 | `/api/admin` | 管理员操作 |
| 健康检查 | `/health` | 服务器状态检测 |

### 炎武班学习中心

| 模块 | 路由前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/learning/auth` | 学习中心注册/登录/JWT（与 DailyRead 隔离） |
| 讲义 | `/api/learning/handouts` | 讲义分发/列表/详情/分类筛选/文件下载；`GET /handouts/recipients` 学生账号列表；`PATCH /handouts/:id/distribute` 追加分发（addLevels + addUserIds，合并去重写回 level_scope/extra_users，向未通知账号补发通知） |
| 作业 | `/api/learning/assignments` | 作业布置/列表/详情/时间窗判断（字段名 `levels` 数组，非 `level_scope`） |
| 作业查询 | `/api/learning/assignments-query` | 按用户/等级查询学员 × 作业提交情况（STAFF 权限；路径用 `-` 避 `/assignments/:id` 匹配冲突） |
| 提交 | `/api/learning/assignments/:id/submit` | 学员作业上传（multipart：Word/Excel/PDF/图片 ≤20MB） |
| 批改 | `/api/learning/submissions/:id/grade` | 教师批改（**POST** 方法，非 PATCH） |
| 提交文件 | `/api/learning/submissions/:id/file` | 提交文件下载（需 JWT 鉴权） |
| 收件箱 | `/api/learning/inbox` | 消息通知列表/已读/批量已读 |
| DailyRead 绑定 | `/api/learning/dr/*` | 学习中心 DailyRead 代理鉴权：绑定/解绑/状态查询（lc token → DailyRead 鉴权 → 写入 `lc_users.dr_user_id`） |
| DailyRead PWA 代理 | `/api/dr/*` | DailyRead PWA 主应用代理路由（经 `lcDrProxyAuth` 注入 `req.drUserId`，按绑定账号转发请求） |
| 完成率 | `/api/learning/dr/completion-rates/students` | 按等级查已绑定学生列表（STAFF 权限） |
| 完成率 | `/api/learning/dr/completion-rates/student` | 查指定学生周/月阅读完成率（`?userId=&view=week\|month&date=YYYY-MM-DD&month=YYYY-MM`，实时统计绑定账号 daily_tasks 打卡数据，自然周/自然月范围） |

---

## 📝 开发规范

| 项目 | 规范 |
|------|------|
| 代码风格 | 2 空格缩进 |
| ArkTS | PascalCase 类名，camelCase 方法/变量 |
| Python | PEP 8，类 PascalCase，方法 snake_case |
| JavaScript | 2 空格缩进，const 优先 |
| 提交信息 | 中文，简洁描述变更 |

---

## 🌐 访问链接

| 服务 | 地址 |
|------|------|
| 门户首页 | https://dailyread.sonnusww.top |
| 用户注册（DailyRead） | https://dailyread.sonnusww.top/register.html |
| 管理后台 | https://dailyread.sonnusww.top/admin/ |
| 炎武班学习中心 | https://dailyread.sonnusww.top/center/ |
| 学习中心登录 | https://dailyread.sonnusww.top/center/login.html |
| DailyRead PWA（学习中心内嵌） | https://dailyread.sonnusww.top/center/dr/bind.html |
| Win 端管理器下载 | https://dailyread.sonnusww.top/downloads/DailyRead_Win.zip |
| API | https://dailyread.sonnusww.top/api |
| 健康检查 | https://dailyread.sonnusww.top/health |
| GitHub | https://github.com/SomnusWei/Dailyread |

> 学习中心不开放注册，由管理员登录后新建账号并设置等级分发学员。默认管理员账号 `somnusweiwei1989`，首次登录建议立即修改密码。

---

## 📝 更新日志

### 2026-09-04

**鸿蒙端（HarmonyOS）：**
- 🔊 **大音频文件化存储**：同步拉取时 >1MB 的 audiobase64 解码写入沙箱文件（`files/audio/{clientId}.m4a`），本地 RDB 行仅存 `file://` 引用；播放（AudioService）识别引用直接 open fd、上传/备份前还原 base64。根治「鸿蒙 RDB 对超长单字段(≈2.7MB)写入失效——insert 返回 rowId 但行不落库」导致的文章无法入库问题（典型：服务端有《刺疟论》/今日任务也有，鸿蒙端却怎么也拉不进来）
- 🎛 **音频控制并入可隐藏顶栏**：阅读页与磨耳跟背页顶栏由单行扩为两行，音频控制（播放/暂停 + 进度 + 时长）作为第二行随 `showBars` 一起显隐（点正文唤出、滚动隐藏），内容区不再内嵌常显音频条
- ⚙️ **多端配置边界收敛（鸿蒙只拉取）**：不再上传「每日阅读时长」「目标完成率」，仅从服务端拉取；`pushConfig` 仅在 `pullConfig` 成功后执行（防本地默认 20 覆盖服务器已设时长）；`pullConfig` 仅在服务端返回有效数值时覆盖本地（去 `||20` 陷阱）；进入设置页时自动拉取服务器配置刷新显示
- 🛡 **分批拉取健壮性**：`pullArticles` 加互斥（防 Splash/Home/定时多套并发交错推进游标）；分批拉取增加失败中断点与最终文章总数核对诊断日志，便于定位漏文

**Windows 端：**
- 🔐 登录「记住账号密码」落地：勾选后账号密码经 QSettings 本地持久化，下次打开登录框自动回填并预勾选（此前复选框仅有 UI 无任何逻辑）

**服务端 / 学习中心：**
- 🎯 **配置写入权收敛**：`PUT /api/config` 改为字段显式才更新（未携带字段保留数据库现值）；学习中心网页代理 `PUT /api/dr/config` 仅接受元数据字段，拦截 `dailyMinutes/targetCheckRate/readerFontSize` 上传——每日阅读时长与目标完成率**只有 Windows 端可修改服务器**
- 🖥 学习中心 DailyRead 内嵌阅读「设置」页改只读：时长/目标率仅展示（标注由 Windows 端维护），阅读字号改为仅保存在本机浏览器 localStorage，不再上传
- 🔄 **阅读任务生成途径收敛为两条**：每天 00:00 定时全量重建（cron）或 Windows 端「重新生成」按钮（`POST /daily-tasks/generate {force:true}`）；移除服务端「修改阅读时长自动 force 重算当日任务」逻辑，当日任务不再因配置变更被意外重置
- 🧹 修复 drProxy `PUT /api/dr/config` 引用未导入 `configRoutes` 的潜在 500；Service Worker 缓存 v7→v8

### 2026-08-31

**新增功能：**
- 🪟 讲义库「分发讲义」改为模态弹窗：点击按钮以弹窗形式打开分发表单 + 我的分发记录，不再在讲义列表下方展开面板
- 🔲 讲义库列表/网格视图切换：新增列表视图与 4 列网格视图两种显示方式，标题栏右侧视图切换按钮（列表/网格图标），用户选择 localStorage 持久化，窄屏响应式降列（1024px→2 列、640px→1 列），网格卡片复用事件委托无需改绑定
- 🔐 删除讲义密码二次确认：删除讲义需输入登录账号密码，前端弹窗（显示当前账号 + 密码输入 + 回车提交 + 聚焦），后端 `DELETE /api/learning/handouts/:id` 路由 bcrypt 校验当前账号密码，密码错误统一返回 403；讲义库列表卡片与「我的分发记录」表格两处删除入口统一走同一弹窗
- 📄 讲义分发标题留空自动用文件名：分发讲义时标题输入框留空也能提交，系统自动以上传 HTML 文件名（去 .html/.htm 扩展名）作为标题；前端提交时取文件名 + 后端 POST `/handouts` 校验放宽（optional checkFalsy）+ 兜底用 originalname，双保险防直接 API 调用绕过

**问题修复/优化：**
- 🔄 Service Worker 缓存策略升级 v6→v7：核心 shell 资源（app.html/app.js/center.css/login.js）改为网络优先（与导航请求同策略），根治「新 HTML + 旧 JS」版本错配导致按钮事件绑定失效；SW 注册加 `updateViaCache:'none'` + `controllerchange` 自动刷新，老标签页新 SW 接管后自动 reload 一次，用户侧无感更新，不再依赖手动硬刷新
- ✏️ 首页炎武班介绍文案微调（创建背景表述调整）

### 2026-08-30

**新增功能：**
- 📊 「完成率」升级为「阅读完成率」：周/月视图独立时间范围选择（周视图选任意一天显示该自然周，月视图直接选月份），数据改为实时统计学员绑定 DailyRead 账号的打卡记录（daily_tasks/daily_task_items 只读查询，不改表结构，不影响 Win/鸿蒙端）
- 📄 讲义「追加分发」：教师/管理员可对已分发讲义追加分发等级或指定账号（lc_handouts 新增 extra_users 字段），自动向未收到过该讲义通知的账号补发通知（去重防打扰），解决分发后新建账号无讲义通知的问题；分发记录表新增「指定账号」列与「追加分发」按钮，弹窗支持等级多选与账号搜索
- ⏱ DailyRead PWA 阅读页新增打卡按钮：进入阅读页 10 秒后才允许打卡（倒计时显示、按钮状态变化、防重复打卡），打卡数据写入所绑定的 DailyRead 账号（服务端零改动，走 /api/dr 代理）
- 🌐 首页炎武班介绍文案按最新文档全量更新（创建背景、育人理念、人才培养、结语）

**问题修复：**
- 🔧 完成率周/月视图原「日期±3/±15 天」范围计算不准，改为自然周（周一~周日）/自然月（1 日~月末），跨月跨年安全
- 🔧 鸿蒙端文章同步分批传输：/api/articles 支持 batch=1 按体积分批返回（约 3MB/批）+ 复合游标 last_modified|id（同秒多篇靠 id 推进防丢数据），鸿蒙端 readTimeout 30s→60s、响应上限 5MB→16MB，避免大数据量拉取超时
- 🔧 Service Worker 缓存版本 v4→v5

### 2026-08-28

**新增功能：**
- 🎓 炎武班学习中心 PWA 上线：独立用户体系（管理员/教师/博士生/研究生/本科生/师承生 6 级），支持 PWA 安装到桌面
- 📄 讲义分发：教师上传 HTML 讲义按等级分发，支持 12 个分类筛选（基础学｜诊断学｜针灸腧穴｜中药｜方剂｜内科｜外科｜妇科｜儿科｜推拿｜养生｜经典）
- 📝 作业布置：富文本编辑器，按等级分发，支持提交时间范围（开始/截止），超期学员仅可查看与评分评语
- 📤 学员作业提交：支持 Word/Excel/PDF/图片格式上传，每人每作业一份，重复提交覆盖旧文件并重置成绩
- ✅ 教师批改：作业布置者可查看提交列表、录入分数与评语，批改结果自动通知学员，支持重新批改
- 📬 消息通知：讲义/作业分发、批改结果自动推送学员收件箱，支持已读/未读筛选与批量已读
- 💾 Win 端新增「全量导出（服务器）」：从服务器拉取账号全量数据（文章含音频/图片 base64、打卡记录、用户配置、今日任务）打包备份
- 🌐 门户首页重构：DailyRead 项目管理与注册入口 + 炎武班学习中心入口双栏布局，展示炎武班团队介绍
- 📚 DailyRead PWA 嵌入学习中心：学习中心导航栏新增「每日阅读」入口，支持学习中心账号绑定 DailyRead 账号后直接在 PWA 内使用（账号单向绑定：lc_users.dr_user_id）
- 🎯 作业管理重构为 4 子标签：作业列表 / 作业查询（按用户/等级筛选） / 作业发布 / 完成率（按等级→学生→周/月柱状图）
- ⏰ 每天 12:00 自动结算 DailyRead PWA 完成率（`drSettle.js` cron），写入 `lc_dr_completion_rates` 表
- 🖥️ Win 端管理器下载入口：学习中心 DailyRead 绑定页底部新增「注册 DailyRead 账号」和「下载 Win 端管理器」卡片链接

**问题修复：**
- 🔧 `/assignments-query` 路由冲突：Express 路由 `/assignments/:id` 先匹配 query 路径，改为 `/assignments-query` 带连字符
- 🔧 `openSubmissionFile` 内联 onclick 找不到函数：函数定义在 IIFE 局部作用域，改为 `window.openSubmissionFile = openSubmissionFile` 全局暴露
- 🔧 POST `/assignments` 字段名：前端传 `levels` 数组而非 `level_scope`
- 🔧 批改接口方法：`POST /submissions/:id/grade` 而非 PATCH
- 🔧 Service Worker 缓存版本升级 v2→v3
- 🔧 三端 since 增量游标按 user_id 隔离：鸿蒙端 ApiClient.ets / Win 端 sync_service.py / 新增账号登录后自动重置 since 触发全量拉取，避免切换账号时继承旧账号游标导致数据不显示
- 🔧 学习中心提交文件下载鉴权：由 `<a href>` 改为 `fetch + JWT`，修复批改/查看文件时报 401 未登录
- 🔧 首页炎武班介绍文案首行缩进 2 个汉字
- 🔧 鸿蒙端 Login.ets 「记住密码」复选框位置右移对齐输入框内容区
- 🔧 服务端内存优化：systemd MemoryMax 384M→512M、V8 heap 256MB→384MB、关闭未托管的 PM2，缓解 504 频繁卡死

### 2026-08-26

**新增功能：**
- 🌐 官方网站上线：首页展示项目介绍、核心功能、系统架构、技术栈，含 GitHub 链接
- 📝 用户注册页面：支持在线注册账号（用于鸿蒙端和 Win 端登录）
- 🔐 管理后台：管理员登录页面 + 数据统计仪表板 + 用户管理（增删改查、重置密码）
- 📖 鸿蒙端"待缓再读"：阅读打卡界面新增按钮，跳过当前文章随机跳转下一篇未完成任务

**问题修复：**
- 🟢 服务器状态指示灯：修复每 10 秒轮询时闪黄的问题，后续检测不再先设为"检测中"
- 🔤 字号本地化：鸿蒙端字号不再上传/拉取服务器，改为各端本地持久化设置
- 📱 音频控件显示：修复纯图模式下打卡阅读页和磨耳跟背页不显示音频控件的问题
- 📊 Win 端表格排序：启用列排序，数值列（如完成率）正确排序

---

## 📄 License

本项目遵循 MIT License。
