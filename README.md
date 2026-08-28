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
- 📄 **讲义分发**：教师/管理员上传 HTML 讲义并按学生等级分发；支持 12 个分类筛选（基础学｜诊断学｜针灸腧穴｜中药｜方剂｜内科｜外科｜妇科｜儿科｜推拿｜养生｜经典）；学员点击在线阅读
- 📝 **作业布置**：富文本编辑器编辑作业，按学生等级分发；支持设置提交时间范围（开始时间/截止时间），超期学员不可再提交，仅可查看作业与评分评语
- 📤 **学员作业提交**：学员在作业区对指定作业上传文件（Word 文档、Excel 表格、PDF 文档、图片），每人每作业一份，重复提交覆盖旧文件并重置成绩；文件大小上限 20MB
- ✅ **教师批改**：作业布置者可查看提交列表，录入分数与评语，批改结果通过收件箱通知学员；支持重新批改
- 📬 **消息通知**：讲义/作业分发、作业批改结果均自动推送到学员收件箱，支持已读/未读筛选与批量已读
- 📊 **分发记录**：教师/管理员可在"我的讲义"与"我的作业"面板查看自己的分发记录与学员提交情况
- 📲 **PWA 支持**：通过 manifest.json + Service Worker 支持安装到桌面/离线访问；静态资源缓存优先 + 后台更新策略，API 与上传内容仅网络获取

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
│   │   │   └── learning.js                 # 炎武班学习中心 API
│   │   ├── middleware/
│   │   │   ├── auth.js                     # 认证中间件（区分 DailyRead / Learning Center token）
│   │   │   └── errorHandler.js
│   │   ├── db/
│   │   │   ├── init.js                     # DailyRead 表初始化与迁移
│   │   │   └── learning_init.js            # 学习中心表初始化（lc_users/lc_handouts/lc_assignments/lc_inbox/lc_submissions）
│   │   ├── utils/response.js
│   │   ├── config.js                       # 配置加载
│   │   ├── db.js                           # 数据库连接池
│   │   ├── cron.js                         # 定时任务（每日 00:00 生成阅读任务）
│   │   └── index.js                        # 服务入口
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
│   │       └── icons/                      # PWA 图标
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
| lc_users | 学习中心用户（username/password_hash/nickname/role 等级） |
| lc_handouts | 讲义（uploader_id/level_scope 分发等级/category 分类 12 选 1/html_file 路径） |
| lc_assignments | 作业（uploader_id/level_scope/start_at/due_at 时间窗/content 富文本） |
| lc_inbox | 收件箱（receiver_id/sender_id/type 类型/title/body/read 已读） |
| lc_submissions | 学员作业提交（assignment_id/student_id 唯一约束/filename/original_name/file_size/score/comment/graded_at/graded_by） |

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
| 讲义 | `/api/learning/handouts` | 讲义分发/列表/详情/分类筛选/文件下载 |
| 作业 | `/api/learning/assignments` | 作业布置/列表/详情/时间窗判断 |
| 提交 | `/api/learning/assignments/:id/submit` | 学员作业上传（multipart：Word/Excel/PDF/图片 ≤20MB） |
| 批改 | `/api/learning/submissions/:id/grade` | 教师批改分数+评语 |
| 提交文件 | `/api/learning/submissions/:id/file` | 提交文件下载（需 JWT 鉴权） |
| 收件箱 | `/api/learning/inbox` | 消息通知列表/已读/批量已读 |

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
| API | https://dailyread.sonnusww.top/api |
| 健康检查 | https://dailyread.sonnusww.top/health |
| GitHub | https://github.com/SomnusWei/Dailyread |

> 学习中心不开放注册，由管理员登录后新建账号并设置等级分发学员。默认管理员账号 `somnusweiwei1989`，首次登录建议立即修改密码。

---

## 📝 更新日志

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

**问题修复：**
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
