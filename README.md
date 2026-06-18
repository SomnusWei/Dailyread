# 每日阅读 · DailyRead

一款面向日常阅读习惯养成的全平台应用，支持文章阅读、概念背诵、穴位记忆、临床笔记、WebDAV 云同步等功能。

---

## 项目概览

本仓库包含四个端的应用项目：

| 项目 | 平台 | 描述 |
|------|------|------|
| [Dailyread_Android](Dailyread_Android/) | Android | 安卓版本 APP（Kotlin + Jetpack Compose） |
| [Dailyread_Harmony](Dailyread_Harmony/) | HarmonyOS | 鸿蒙版本 APP（ArkTS + ArkUI） |
| [Dailyread_win_article_concept_manager](Dailyread_win_article_concept_manager/) | Windows | Win 端配套数据管理工具（Python + PyQt） |
| [Dailyread_pwa_article_concept_manager](Dailyread_pwa_article_concept_manager/) | Web | 网页版配套数据管理工具（Vue 3 + TypeScript + PWA） |

---

## 功能对比

| 功能 | Android | HarmonyOS | Windows | PWA |
|------|:--------:|:---------:|:-------:|:---:|
| 文章管理 | ✅ | ✅ | ✅ | ✅ |
| 图片上传（WebP 压缩） | ❌ | ✅ | ✅ | ✅ |
| 概念管理 | ✅ | ✅ | ✅ | ✅ |
| 穴位背诵 | ✅ | ✅ | ❌ | ❌ |
| 临床笔记 | ❌ | ✅ | ✅ | ✅ |
| 每日任务生成 | ✅ | ✅ | ❌ | ❌ |
| 阅读打卡 | ✅ | ✅ | ❌ | ❌ |
| 热力图统计 | ✅ | ❌ | ❌ | ❌ |
| 本地备份/恢复 | ✅ | ✅ | ✅ | ✅ |
| WebDAV 同步 | ❌ | ✅ | ✅ | ✅ |
| 用户认证 | ❌ | ❌ | ❌ | ✅ |
| PWA 离线访问 | ❌ | ❌ | ❌ | ✅ |
| Windows EXE | ❌ | ❌ | ✅ | ❌ |

---

## 核心功能说明

### 文章管理
- 添加、编辑、删除文章
- 自动统计汉字字数
- 图片上传（自动压缩为 WebP 格式，25KB 以下）
- 阅读状态管理（正在阅读/必读）
- 打卡率和完成率跟踪

### 概念背诵
- 分类、学科、章节管理
- 快速粘贴添加（支持 `|` 或 `,` 分隔）
- 批量导入/导出 JSON

### 临床笔记
- 病机、治法、处方、备注字段
- 学习状态切换
- 数据同步支持

### WebDAV 同步
支持与坚果云、Nextcloud 等 WebDAV 协议云存储服务同步数据。

**坚果云配置示例：**
- 服务器地址：`https://dav.jianguoyun.com/dav/`
- 远程路径：`/DailyRead`

---

## 数据格式

所有端使用统一的 JSON 备份格式：

```json
{
  "version": 6,
  "exportTime": "2026-06-17T10:00:00.000Z",
  "dataType": "daily_read_backup",
  "articles": [...],
  "concepts": [...],
  "clinicalNotes": [...]
}
```

---

## 各端详情

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
- **在线访问**：http://47.95.205.216/

---

## 许可证

MIT License
