# 📚 每日阅读 · DailyRead

一款面向日常阅读习惯养成的全平台应用，支持文章阅读、概念背诵、穴位记忆、临床笔记、WebDAV 云同步等功能。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Android%20%7C%20HarmonyOS%20%7C%20Windows%20%7C%20Web-blue.svg)]()

---

## 📁 项目概览

本仓库包含四个端的应用项目：

| 项目 | 平台 | 描述 |
|------|------|------|
| [Dailyread_Android](Dailyread_Android/) | Android | 安卓版本 APP（Kotlin + Jetpack Compose） |
| [Dailyread_Harmony](Dailyread_Harmony/) | HarmonyOS | 鸿蒙版本 APP（ArkTS + ArkUI） |
| [Dailyread_win_article_concept_manager](Dailyread_win_article_concept_manager/) | Windows | Win 端配套数据管理工具（Python + PyQt） |
| [Dailyread_pwa_article_concept_manager](Dailyread_pwa_article_concept_manager/) | Web | 网页版配套数据管理工具（Vue 3 + TypeScript + PWA） |

---

## ✨ 功能对比

| 功能 | Android | HarmonyOS | Windows | PWA |
|------|:--------:|:---------:|:-------:|:---:|
| 文章管理 | ✅ | ✅ | ✅ | ✅ |
| 图片上传（WebP 压缩） | ❌ | ✅ | ✅ | ✅ |
| 概念管理 | ✅ | ✅ | ✅ | ✅ |
| 穴位背诵 | ✅ | ✅ | ❌ | ❌ |
| 临床笔记 | ❌ | ✅ | ✅ | ✅ |
| 每日任务生成 | ✅ | ✅ | ❌ | ❌ |
| 阅读打卡 | ✅ | ✅ | ❌ | ❌ |
| 自动 WebDAV 同步（完成任务后） | ❌ | ✅ | ❌ | ❌ |
| 热力图统计 | ✅ | ❌ | ❌ | ❌ |
| 本地备份/恢复 | ✅ | ✅ | ✅ | ✅ |
| WebDAV 同步 | ❌ | ✅ | ✅ | ✅ |
| 用户认证 | ❌ | ❌ | ❌ | ✅ |
| PWA 离线访问 | ❌ | ❌ | ❌ | ✅ |
| Windows EXE | ❌ | ❌ | ✅ | ❌ |

---

## 🚀 核心功能说明

### 📖 文章管理
- 添加、编辑、删除文章
- 自动统计汉字字数
- 图片上传（自动压缩为 WebP 格式，25KB 以下）
- 阅读状态管理（正在阅读/必读）
- 打卡率和完成率跟踪

### 📝 概念背诵
- 分类、学科、章节管理
- 快速粘贴添加（支持 `|` 或 `,` 分隔）
- 批量导入/导出 JSON

### 🏥 临床笔记
- 病机、治法、处方、备注字段
- 学习状态切换
- 数据同步支持

### ☁️ WebDAV 同步
支持与坚果云、Nextcloud 等 WebDAV 协议云存储服务同步数据。

**坚果云配置示例：**
- 服务器地址：`https://dav.jianguoyun.com/dav/`
- 远程路径：`/DailyRead`

---

## 🔧 核心代码示例

### WebDAV 同步服务

```typescript
// src/services/webdav.ts
export const webdavService = {
  // 测试连接
  async testConnection(config: WebDavConfig): Promise<boolean> {
    const client = createClient(getServerUrl(config.serverUrl), {
      username: config.username,
      password: config.password
    })
    await client.exists(config.remotePath)
    return true
  },
  
  // 上传备份
  async uploadBackup(config: WebDavConfig, data: BackupData): Promise<void> {
    const client = createClient(getServerUrl(config.serverUrl), {
      username: config.username,
      password: config.password
    })
    const content = JSON.stringify(data, null, 2)
    await client.putFileContents(`${config.remotePath}/daily_read_backup_windows.json`, content, {
      overwrite: true
    })
  },
  
  // 下载备份（处理 ArrayBuffer 转字符串）
  async downloadBackup(config: WebDavConfig): Promise<BackupData> {
    const content = await client.getFileContents(filePath)
    let jsonString = typeof content === 'string' 
      ? content 
      : new TextDecoder('utf-8').decode(content as ArrayBuffer)
    return JSON.parse(jsonString)
  }
}
```

### 文章数据服务

```typescript
// src/services/article.ts
export const articleService = {
  async getAll(): Promise<Article[]> {
    const data = localStorage.getItem(STORAGE_KEY)
    return data ? JSON.parse(data) : []
  },
  
  async create(article: Omit<Article, 'id' | 'createTime' | 'lastModified'>): Promise<Article> {
    const articles = await this.getAll()
    const now = new Date().toISOString()
    const newArticle: Article = {
      ...article,
      id: articles.length > 0 ? Math.max(...articles.map(a => a.id)) + 1 : 1,
      createTime: now,
      lastModified: now
    }
    articles.push(newArticle)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(articles))
    return newArticle
  },
  
  async bulkDelete(ids: number[]): Promise<void> {
    const articles = await this.getAll()
    const filtered = articles.filter(a => !ids.includes(a.id))
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered))
  }
}
```

### 全量备份服务

```typescript
// src/services/backup.ts
export const backupService = {
  async exportToJSON(): Promise<string> {
    const [articles, concepts, clinicalNotes] = await Promise.all([
      articleService.getAll(),
      conceptService.getAll(),
      clinicalService.getAll()
    ])
    
    const backupData: BackupData = {
      version: 6,
      exportTime: new Date().toISOString(),
      dataType: 'daily_read_backup',
      articles,
      concepts,
      clinicalNotes
    }
    
    return JSON.stringify(backupData, null, 2)
  }
}
```

---

## 📊 数据格式

所有端使用统一的 JSON 备份格式：

```json
{
  "version": 6,
  "exportTime": "2026-06-17T10:00:00.000Z",
  "dataType": "daily_read_backup",
  "articles": [
    {
      "id": 1,
      "title": "文章标题",
      "content": "文章内容",
      "chineseChars": 1280,
      "isReading": true,
      "completionRate": 85,
      "createTime": "2026-01-01T00:00:00.000Z"
    }
  ],
  "concepts": [...],
  "clinicalNotes": [...]
}
```

---

## 📱 各端详情

### Android APP
- **位置**：[Dailyread_Android](Dailyread_Android/)
- **技术栈**：Kotlin + Jetpack Compose + Room + Hilt
- **特色**：热力图统计、自适应布局

### HarmonyOS APP
- **位置**：[Dailyread_Harmony](Dailyread_Harmony/)
- **技术栈**：ArkTS + ArkUI + SQLite
- **特色**：完整的文章图片支持、智能每日任务生成

### Windows 管理工具
- **位置**：[Dailyread_win_article_concept_manager](Dailyread_win_article_concept_manager/)
- **技术栈**：Python 3.14+ + PyQt 6
- **特色**：快捷键支持、批量操作、EXE 打包

### PWA 网页版
- **位置**：[Dailyread_pwa_article_concept_manager](Dailyread_pwa_article_concept_manager/)
- **技术栈**：Vue 3 + TypeScript + Vite + TailwindCSS + Pinia
- **特色**：用户认证、PWA 离线访问、响应式设计

---

## 📄 许可证

MIT License

---

## 📝 更新日志

### 2026-06-20
- **Win**: 优化文章编辑对话框布局——左右分栏显示（左侧25%为图片设置和选项，右侧75%为文章内容）
- **Win**: 文章内容输入框字号增大为14pt，便于编辑
- **Win**: 概念编辑对话框和临床笔记编辑对话框打开时居中显示
- **Win**: 文章添加/编辑成功提示改为状态栏显示（3秒），避免弹窗阻塞操作
- **Win**: 修复文章编辑确认后应用卡死闪退的问题（statusBar调用错误）

### 2026-06-19
- **HarmonyOS**: 新增自动 WebDAV 同步功能——完成今日全部任务后自动触发云端备份，当天仅执行一次
- **HarmonyOS**: 修改每日任务字数计算系数，从 250 字/分钟调整为 100 字/分钟
- **HarmonyOS**: 修复首页目标字数显示与任务生成不一致的问题

### 2026-06-18
- **PWA**: 移除富文本编辑功能，恢复纯文本编辑
- **HarmonyOS**: 修复 RichText 组件样式属性错误

### 2026-06-17
- **PWA**: 添加后端服务（Node.js + Express + SQLite），支持用户注册/登录和 WebDAV 配置服务器端存储
- **PWA**: 优化图片压缩算法，参考鸿蒙端多级尺寸+质量组合策略
- **Win**: 添加文章富文本编辑功能（粗体、斜体、下划线、字体颜色、背景颜色）
- **HarmonyOS**: 添加 RichText 组件支持富文本显示
