# DailyRead · 每日阅读

> 面向日常阅读习惯养成的跨平台应用套件，包含鸿蒙端 APP、Windows 端管理器和云端同步服务。

---

## 📖 项目简介

DailyRead 是一套帮助用户养成每日阅读习惯的工具，支持文章阅读、概念背诵、临床笔记、人体穴位记忆等学习场景。整个项目由三个子项目组成，覆盖移动端阅读、桌面端管理和云端数据同步。

### 核心功能

- 📚 **文章阅读**：文章管理、图片上传（WebP 压缩）、每日自动生成阅读任务
- 🧠 **概念背诵**：按分类/学科/章节管理，随机背诵模式
- 🏥 **临床笔记**：病机、治法、处方结构化管理，随机背诵
- 📍 **穴位记忆**：内置常用穴位库，随机抽查
- ☁️ **多端同步**：通过后端 API 或 WebDAV 实现鸿蒙端与 Windows 端数据互通
- 💾 **数据备份**：支持 JSON 导入/导出，一键迁移

---

## 🏗 技术栈

| 子项目 | 语言/框架 | 说明 |
|--------|-----------|------|
| Dailyread_Harmony | ArkTS / ArkUI | 鸿蒙端移动应用 |
| Dailyread_win_article_concept_manager | Python / PyQt 6 | Windows 桌面管理工具 |
| dailyread-server | Node.js / Express / MySQL | 后端同步服务 |

---

## 📂 目录结构

```
DailyRead/
├── Dailyread_Harmony/                      # 鸿蒙端 APP
│   ├── entry/
│   │   └── src/main/ets/
│   │       ├── pages/                      # 页面（首页、阅读、设置等）
│   │       ├── model/                      # 数据模型
│   │       ├── repository/                 # 数据访问层
│   │       ├── service/                    # 业务服务层
│   │       └── database/                   # SQLite 数据库
│   ├── AppScope/                           # 应用级资源
│   └── README.md                           # 鸿蒙端详细文档
│
├── Dailyread_win_article_concept_manager/   # Windows 端管理器
│   ├── article_concept_manager.py          # 主程序
│   ├── api_client.py                       # 后端 API 客户端
│   ├── sync_service.py                     # WebDAV 同步服务
│   ├── app.spec                            # PyInstaller 打包配置
│   ├── requirements.txt                    # 依赖列表
│   └── README.md                           # Windows 端详细文档
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

## 🔗 子项目关系

```
┌─────────────────┐     API / WebDAV     ┌─────────────────┐
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

- **鸿蒙端** 与 **Windows 端** 可通过 **后端 API** 或 **WebDAV** 双向同步
- 两端也可独立使用 **JSON 导入/导出** 进行数据迁移
- 后端提供用户体系、数据持久化和增量同步能力

---

## 🗄 数据库设计（后端）

后端使用 MySQL，主要表结构：

| 表名 | 说明 |
|------|------|
| users | 用户表（用户名、密码、角色） |
| articles | 文章表（多端同步字段 `client_id` + `user_id` 唯一） |
| checkins | 打卡记录表 |
| daily_tasks | 每日任务表 |
| daily_task_items | 每日任务条目表 |
| user_configs | 用户配置表 |

详见 [schema.sql](dailyread-server/schema.sql)。

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

## 📄 License

本项目遵循 MIT License。
