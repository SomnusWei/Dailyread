# DailyRead · 每日阅读

> 面向日常阅读习惯养成的跨平台应用套件，包含鸿蒙端 APP、Windows 端管理器和云端同步服务。

---

## 📖 项目简介

DailyRead 是一套帮助用户养成每日阅读习惯的工具，支持文章阅读、音频朗读、磨耳跟背等学习场景。整个项目由三个子项目组成，覆盖移动端阅读、桌面端管理和云端数据同步。

### 核心功能

- 📚 **文章管理**：文章增删改查、图片上传（WebP 压缩）、批量编辑、表格排序
- 📋 **每日阅读**：每日自动生成阅读任务，打卡记录，完成率统计，支持"待缓再读"跳过当前文章
- 🔊 **音频朗读**：文章支持 m4a 音频，Win 端录入转码（ffmpeg）、鸿蒙端 AVPlayer 自动播放/循环播放、三端同步透传
- 🎧 **磨耳跟背**：鸿蒙端独立底栏入口，只展示有音频的文章，进入简化阅读页专注跟听跟背
- ⚙️ **多端配置同步**：每日阅读时长、目标完成率、自动播放/循环播放等配置双端共享、实时同步（字号为各端本地设置，不同步）
- ☁️ **多端同步**：通过后端 API 实现鸿蒙端与 Windows 端数据实时互通
- 💾 **数据备份**：支持 JSON 导入/导出，一键迁移
- 🟢 **服务器状态监控**：五端（鸿蒙首页/文章管理/磨耳跟背/随心阅读/设置 + Win 端状态栏）实时显示服务器连通状态
- 🌐 **官方网站**：项目官网展示项目介绍、功能特性、技术架构，支持在线注册账号
- 🔐 **管理后台**：管理员登录后台，查看数据统计、用户管理（增删改查）

---

## 🏗 技术栈

| 子项目 | 语言/框架 | 说明 |
|--------|-----------|------|
| Dailyread_Harmony | ArkTS / ArkUI | 鸿蒙端移动应用 |
| Dailyread_win_article_concept_manager | Python / PyQt 6 | Windows 桌面管理工具 |
| dailyread-server | Node.js / Express / MySQL | 后端同步服务 + 官网静态页面 |

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
│   │       ├── service/                     # 业务服务层（含 AudioService 音频播放）
│   │       └── database/                   # SQLite 数据库（版本化迁移）
│   └── README.md                           # 鸿蒙端详细文档
│
├── Dailyread_win_article_concept_manager/   # Windows 端管理器
│   ├── article_concept_manager.py          # 主程序（含音频转码、批量导入、服务器状态指示灯）
│   ├── api_client.py                       # 后端 API 客户端
│   ├── sync_service.py                     # 同步服务
│   ├── app.spec                            # PyInstaller 打包配置
│   └── requirements.txt                    # 依赖列表
│
├── dailyread-server/                       # 后端服务
│   ├── src/
│   │   ├── routes/                         # API 路由
│   │   ├── middleware/                     # 中间件（认证、错误处理）
│   │   ├── utils/                          # 工具函数
│   │   ├── config.js                       # 配置加载
│   │   ├── db.js                           # 数据库连接
│   │   ├── cron.js                         # 定时任务
│   │   └── index.js                        # 服务入口
│   ├── public/                             # 前端静态文件（官网 + 注册 + 管理后台登录）
│   │   ├── index.html                      # 官网首页
│   │   ├── register.html                   # 用户注册页
│   │   ├── login.html                      # 管理员登录页
│   │   ├── admin.html                      # 管理后台（统计 + 用户管理）
│   │   ├── css/style.css                   # 全站样式
│   │   └── js/                             # 前端交互脚本
│   ├── schema.sql                          # 数据库建表脚本
│   ├── .env.example                        # 环境变量模板
│   └── package.json
│
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
npm run init-db

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

---

## 🗄 数据库设计（后端）

后端使用 MySQL，主要表结构：

| 表名 | 说明 |
|------|------|
| users | 用户表（用户名、密码、角色） |
| articles | 文章表（多端同步字段 `client_id` + `user_id` 唯一；含 `imagewebp` 图片、`audiobase64` 音频、`iscontent` 是否显示内容） |
| checkins | 打卡记录表 |
| daily_tasks | 每日任务表 |
| daily_task_items | 每日任务条目表 |
| user_configs | 用户配置表（`daily_minutes` 每日阅读时长、`target_check_rate` 目标完成率、`reader_font_size` 字号、`auto_play_audio` 自动播放、`loop_audio` 循环播放等） |

---

## 📡 API 路由

| 模块 | 路由前缀 | 说明 |
|------|----------|------|
| 认证 | `/api/auth` | 注册、登录、JWT 签发 |
| 文章 | `/api/articles` | 文章 CRUD、批量同步 |
| 打卡 | `/api/checkins` | 打卡记录管理 |
| 配置 | `/api/config` | 用户配置读写 |
| 每日任务 | `/api/daily-tasks` | 任务生成与同步 |
| 管理 | `/api/admin` | 管理员操作 |
| 健康检查 | `/health` | 服务器状态检测 |

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
| 官网首页 | https://dailyread.sonnusww.top |
| 用户注册 | https://dailyread.sonnusww.top/register.html |
| 管理后台 | https://dailyread.sonnusww.top/admin/ |
| API | https://dailyread.sonnusww.top/api |
| 健康检查 | https://dailyread.sonnusww.top/health |
| GitHub | https://github.com/SomnusWei/Dailyread |

---

## � 更新日志

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

## �📄 License

本项目遵循 MIT License。
