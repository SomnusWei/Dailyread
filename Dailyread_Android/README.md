
# 每日阅读 Android 应用

一款简洁高效的阅读打卡应用，帮助你坚持每日阅读习惯。

## 功能特性

- 📚 文章管理：添加、编辑、删除文章
- 📋 每日任务：智能推荐今日阅读任务
- ✅ 打卡系统：记录每日阅读情况
- 📊 阅读统计：热力图展示阅读习惯
- 💾 本地数据导入导出：备份你的阅读数据
- ☁️ 网盘同步：支持百度网盘、阿里云盘、夸克网盘
- 📱 自适应布局：适配各种设备尺寸
- 🔄 自动旋转：支持横竖屏切换

## 技术栈

- **语言**：Kotlin
- **UI框架**：Jetpack Compose
- **架构**：MVVM + Clean Architecture
- **数据库**：Room
- **依赖注入**：Hilt
- **异步处理**：Kotlin Coroutines + Flow
- **导航**：Navigation Compose

## 项目结构

```
app/
├── data/
│   ├── local/              # 本地数据
│   │   ├── database/      # Room数据库
│   │   └── preferences/   # 应用首选项
│   └── repository/        # 数据仓库
├── domain/                # 领域层
│   ├── model/            # 数据模型
│   └── usecase/          # 业务逻辑
├── ui/                    # UI层
│   ├── theme/            # 主题
│   ├── components/       # 公共组件
│   ├── screens/          # 页面
│   └── navigation/       # 导航
└── di/                   # 依赖注入
```

## 开发指南

### 环境要求

- Android Studio Hedgehog 或更高版本
- JDK 17
- Android SDK 34

### 构建项目

1. 克隆项目
2. 使用 Android Studio 打开
3. 同步 Gradle
4. 连接设备或启动模拟器
5. 点击 Run 按钮

### 核心模块说明

#### 文章管理
- 支持添加和编辑文章
- 自动统计文章字数
- 可配置是否加入阅读计划

#### 每日任务
- 基于打卡率智能推荐
- 每日生成新的任务列表
- 支持任务阅读和打卡

#### 数据备份
- 导出为 JSON 格式
- 支持从备份文件导入数据

## 许可证

MIT License
