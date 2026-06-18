# 每日阅读 · 文章与概念管理器

用于「每日阅读」APP 的本地数据管理工具，支持文章、概念、临床笔记的增删改查、数据备份与恢复、WebDAV 同步等功能。

配套使用的鸿蒙APP：<https://github.com/somnuskwelaweiwei1989/DailyRead_Harmony>

本项目：<https://github.com/somnuskwelaweiwei1989/article-concept-manager>

## 📋 功能概览

- **文章管理**：增删改查、自动统计汉字数、图片上传（WebP 自动压缩到 25KB 以下）、快速粘贴添加（支持 `,` 或 `|` 分隔）、批量删除、导入/导出 JSON
- **概念管理**：增删改查、分类/学科/章节管理、快速粘贴添加、批量删除、导入/导出 JSON
- **临床笔记管理**：增删改查、病机/治法/处方/备注字段、快速粘贴、导入/导出 JSON
- **整体备份/恢复**：一键导出包含文章、概念、临床笔记的完整备份文件
- **WebDAV 同步**：支持坚果云、Nextcloud 等服务的全量数据上传下载
- **本地持久化**：所有数据自动保存到 `app_data.json`
- **快捷键支持**：支持自定义快捷键，默认 `Ctrl+N` 添加、`Ctrl+F` 搜索
- **文章默认设置**：在设置页面可修改新增文章时 `正在阅读`、`必读`、`使用独立目标完成率` 的默认值
- **窗口记忆**：自动记忆主窗口和弹窗的位置与大小

## 🚀 运行方式

### 方式一：直接运行 EXE（推荐）

```bash
# 双击运行打包好的可执行文件
dist/每日阅读管理器.exe
```

### 方式二：使用 Python 运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python article_concept_manager.py
```

## 🖥️ 界面说明

启动后，主界面包含五个 Tab：

### 📖 文章管理

- **列**：ID / 标题 / 汉字数 / 在读 / 独立打卡率 / 独立目标完成率 / 必读 / 累计打卡天数 / 完成率 / 图片 / 内容
- **操作**：
  - `添加`：新建一篇文章（支持上传图片，自动压缩为 WebP 并嵌入 base64）
  - `编辑`：编辑选中的文章（双击行或点击按钮）
  - `批量删除`：删除选中的多条记录（支持 Ctrl/Shift 多选）
  - `快速粘贴`：按 `标题,内容` 或 `标题|内容` 格式批量添加，快速粘贴的文章 `isReading` 默认为 `true`
  - `导入 JSON`：从 JSON 文件批量导入
  - `导出 JSON`：导出当前文章列表

### 💡 概念管理

- **列**：ID / 标题 / 分类 / 学科 / 章节 / 内容
- **操作**：与文章管理类似
- **快速粘贴格式**：`标题|分类|学科|章节|内容`（字段可留空），添加的概念 `isReading` 默认为 `true`

### 🏥 临床笔记

- **列**：ID / 标题 / 病机 / 治法 / 处方 / 学习中
- **操作**：添加、编辑、批量删除、快速粘贴、导入/导出 JSON
- **快速粘贴格式**：每行 `标题|病机|治法|处方|备注`（字段可留空）；也支持英文逗号 `,` 分隔

### 💾 备份与恢复

- `导出备份`：导出完整备份文件 `daily_read_backup_windows.json`（包含文章、概念、临床笔记）
- `导入备份`：从备份文件整体恢复（会覆盖当前数据）
- `WebDAV 上传`：上传备份到远程服务器
- `WebDAV 下载`：从远程服务器下载并恢复
- `配置 WebDAV`：设置服务器地址、账号、密码等信息

### ⚙️ 设置

- **快捷键设置**：自定义添加和搜索的快捷键（文章/概念/临床笔记分别配置）
- **文章默认设置**：新增文章时 `正在阅读`、`必读`、`使用独立目标完成率` 的默认值
- **关于**：显示版本信息和功能说明

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 添加文章/概念/临床笔记 |
| `Ctrl+F` | 聚焦搜索框 |
| `Delete` | 删除选中项 |
| `Esc` | 关闭弹窗 |

> ⚠️ 快捷键可在设置页面自定义修改

## 📊 数据结构

### 文章结构

```json
{
  "id": 1,
  "title": "文章标题",
  "content": "正文内容……",
  "contentHtml": "",
  "chineseChars": 128,
  "fontFamily": "default",
  "fontSize": 16,
  "isReading": true,
  "isRequired": false,
  "useIndependentCheckRate": false,
  "independentCheckRate": 0,
  "checkInDays": 0,
  "completionRate": 0,
  "imagewebp": "UklGRtIBAABXRUJQVlA4T...(base64 encoded WebP)",
  "createTime": "2026-06-13T10:00:00",
  "lastModified": "2026-06-13T12:30:00"
}
```

### 概念结构

```json
{
  "id": 1,
  "title": "概念标题",
  "category": "分类",
  "subject": "学科",
  "chapter": "章节",
  "content": "概念的具体内容……",
  "isReading": false,
  "createTime": "2026-06-13T10:00:00",
  "lastModified": "2026-06-13T12:30:00"
}
```

### 临床笔记结构

```json
{
  "id": 1,
  "title": "感冒·风寒束表证",
  "pathogenesis": "风寒外束，卫阳被郁",
  "treatment": "辛温解表",
  "prescription": "麻黄汤加减",
  "notes": "表实无汗者用此方",
  "isReading": true,
  "createTime": "2026-06-13T10:00:00",
  "lastModified": "2026-06-13T12:30:00"
}
```

### 完整备份格式（与鸿蒙端互通）

```json
{
  "version": 2,
  "dataType": "daily_read_backup",
  "articles": [ ... ],
  "concepts": [ ... ],
  "clinicalNotes": [ ... ]
}
```

## 🔄 备份与恢复

### 备份

1. 切换到「💾 备份与恢复」Tab
2. 点击「导出备份」
3. 选择保存路径（建议命名为 `daily_read_backup_windows.json`）

### 恢复

1. 切换到「💾 备份与恢复」Tab
2. 点击「导入备份」
3. 选择之前导出的备份文件

> ⚠️ 导入备份会覆盖当前全部数据，建议先导出一份备份再操作

## ☁️ WebDAV 同步

### 支持的服务

- **坚果云**（推荐）：`https://dav.jianguoyun.com/dav/`
- **Nextcloud**：`https://<your-domain>/remote.php/dav/files/<user>/`
- 其他遵循 WebDAV 协议的服务

### 配置步骤

1. 打开「💾 备份与恢复」Tab → 点击「配置 WebDAV」
2. 填入服务器地址、用户名、密码、远程文件名
3. 点击「保存并使用」

配置会保存到 `webdav_config.json`，下次启动自动读取。
WebDAV 上传的文件格式与本地备份文件完全一致，可直接在鸿蒙端或其他设备下载读取。

## 📁 文件说明

| 文件 | 用途 |
|------|------|
| `article_concept_manager.py` | 主程序文件 |
| `app_data.json` | 本地数据存储（自动生成） |
| `daily_read_backup_windows.json` | 备份文件样例 |
| `webdav_config.json` | WebDAV 配置文件（自动生成） |
| `logo.png` | 应用图标 |
| `app.spec` | PyInstaller 打包配置 |
| `requirements.txt` | 依赖列表 |
| `dist/每日阅读管理器.exe` | 打包后的可执行文件 |

## 🛠️ 技术栈

- **Python 3.14+**
- **PyQt 6**：GUI 框架
- **PyInstaller**：打包工具
- **Requests**：HTTP 请求（WebDAV）

## 📝 开发说明

### 打包 EXE

```bash
# 使用 PyInstaller 打包
python -m PyInstaller --clean --noconfirm app.spec

# 生成的可执行文件位于 dist/ 目录
```

### 依赖安装

```bash
pip install PyQt6 requests
```

## 📄 许可证

MIT License
