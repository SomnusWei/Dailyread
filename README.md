# 每日阅读 (DailyRead)

一个跨平台的文章管理和阅读应用，支持鸿蒙、Windows 和 Web (PWA) 三端，提供文章管理、随机阅读、数据备份和 WebDAV 同步功能。

## 项目简介

每日阅读是一个专注于个人知识管理的应用，帮助用户收集、整理和阅读文章内容。支持多端数据同步，让您的知识随时随地可用。

## 主要功能

### 📱 鸿蒙端

- **文章管理**：创建、编辑、删除文章，支持富文本编辑
- **随机阅读**：从文章库中随机抽取文章进行阅读
- **数据备份**：本地备份和恢复功能
- **WebDAV 同步**：支持坚果云、Nextcloud 等云存储服务
- **每日任务**：设置每日阅读目标，打卡记录

### 💻 Windows 端

- **文章管理**：完整的文章 CRUD 操作
- **数据备份**：JSON 格式备份和恢复
- **WebDAV 同步**：云端数据同步
- **本地存储**：SQLite 数据库存储

### 🌐 PWA 端

- **用户认证**：注册、登录功能
- **文章管理**：在线管理文章内容
- **数据备份**：本地备份和云端同步
- **响应式设计**：支持桌面和移动设备
- **离线支持**：PWA 离线功能

## 技术栈

### 鸿蒙端
- **框架**：HarmonyOS ArkTS
- **UI**：ArkUI
- **数据库**：Room 数据库
- **网络**：WebDAV 协议

### Windows 端
- **框架**：Python + PyQt6
- **数据库**：SQLite
- **网络**：WebDAV 协议
- **打包**：PyInstaller

### PWA 端
- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **状态管理**：Pinia
- **路由**：Vue Router
- **样式**：Tailwind CSS
- **PWA**：Vite PWA Plugin
- **后端**：Node.js + Express + SQLite

## 项目结构

```
DailyRead/
├── Dailyread_Harmony/          # 鸿蒙端应用
│   ├── entry/src/main/ets/
│   │   ├── database/          # 数据库相关
│   │   ├── model/             # 数据模型
│   │   ├── pages/             # 页面
│   │   ├── repository/        # 数据仓库
│   │   └── service/           # 业务服务
│   └── 背临床_背概念_背穴位功能说明.md
├── Dailyread_win_article_concept_manager/  # Windows 端应用
│   ├── article_concept_manager.py
│   ├── app.spec
│   └── requirements.txt
├── Dailyread_pwa_article_concept_manager/  # PWA 端应用
│   ├── src/
│   │   ├── components/        # 组件
│   │   ├── services/          # 服务
│   │   ├── stores/            # 状态管理
│   │   ├── views/             # 页面
│   │   └── utils/             # 工具函数
│   ├── server/                # 后端服务
│   └── scripts/               # 部署脚本
└── .gitignore
```

## 安装和使用

### 鸿蒙端

1. 使用 DevEco Studio 打开 `Dailyread_Harmony` 项目
2. 连接鸿蒙设备或启动模拟器
3. 点击运行按钮安装应用

### Windows 端

1. 安装 Python 3.8+
2. 安装依赖：
   ```bash
   cd Dailyread_win_article_concept_manager
   pip install -r requirements.txt
   ```
3. 运行应用：
   ```bash
   python article_concept_manager.py
   ```

### PWA 端

#### 本地开发

1. 安装 Node.js 18+
2. 安装依赖：
   ```bash
   cd Dailyread_pwa_article_concept_manager
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```

#### 生产部署

1. 构建项目：
   ```bash
   npm run build
   ```

2. 部署到服务器：
   ```bash
   python scripts/deploy_server.py
   ```

3. 配置 Nginx：
   ```bash
   python scripts/configure_nginx.py
   ```

## 数据同步

### 备份格式

项目使用统一的 JSON 备份格式（version 7），仅包含文章数据：

```json
{
  "version": 7,
  "exportTime": "2024-06-21T00:00:00.000Z",
  "dataType": "daily_read_backup",
  "articles": [
    {
      "id": 1,
      "title": "文章标题",
      "content": "文章内容",
      "tags": ["标签1", "标签2"],
      "created_at": "2024-06-21T00:00:00.000Z",
      "updated_at": "2024-06-21T00:00:00.000Z"
    }
  ]
}
```

### WebDAV 配置

支持以下 WebDAV 服务：

- **坚果云**：`https://dav.jianguoyun.com/dav/`
- **Nextcloud**：`https://your-nextcloud.com/remote.php/webdav/`
- **其他 WebDAV 服务**：支持标准 WebDAV 协议的服务

## 部署说明

### PWA 端部署

PWA 端已部署到服务器：`http://47.95.205.216`

#### 服务器配置

- **操作系统**：Ubuntu
- **Web 服务器**：Nginx
- **后端服务**：Node.js (端口 3001)
- **数据库**：SQLite

#### Nginx 配置

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;

    root /var/www/html;
    index index.html index.htm index.nginx-debian.html;

    server_name _;

    # WebDAV 配置 API
    location = /api/webdav/config {
        proxy_pass http://localhost:3001/api/webdav/config;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # WebDAV 反向代理
    location /api/webdav/ {
        proxy_pass https://dav.jianguoyun.com/dav/;
        proxy_ssl_server_name on;
        proxy_ssl_protocols TLSv1.2 TLSv1.3;
        proxy_set_header Host dav.jianguoyun.com;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
        proxy_buffering off;
    }

    # API 路径
    location /api/ {
        proxy_pass http://localhost:3001/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # 前端应用路由
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## 更新日志

### v2.0.0 (2024-06-21)

**重大更新**

- ✨ 移除背临床、背穴位、背概念功能
- 🔧 优化三端数据同步，统一备份格式
- 🚀 PWA 端重新部署，修复 API 路由问题
- 📱 鸿蒙端修改底栏为：首页 | 文章管理 | 随心阅读 | 设置
- 🌐 PWA 端添加用户认证功能
- 🐛 修复 Nginx 配置问题，支持 SPA 路由
- 📝 添加功能说明文档

**技术改进**

- 鸿蒙端：优化 WebDAV 同步逻辑，仅同步文章数据
- Win端：简化数据模型，移除不必要功能
- PWA端：修复 API_BASE_URL 配置，添加 Nginx 反向代理支持

### v1.0.0

- 初始版本发布
- 支持三端基本功能
- WebDAV 同步功能

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证。

## 联系方式

- 项目地址：https://github.com/SomnusWei/Dailyread
- 在线体验：http://47.95.205.216

## 致谢

感谢所有为本项目做出贡献的开发者！