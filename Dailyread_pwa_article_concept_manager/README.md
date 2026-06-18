# 每日阅读 · PWA 网页版管理器

基于 Vue 3 + TypeScript 开发的渐进式网页应用（PWA），支持文章、概念、临床笔记的增删改查、数据备份与恢复、WebDAV 同步等功能。

配套使用的鸿蒙APP：https://github.com/somnuskwelawei1989/DailyRead_Harmony

## 功能概览

- **用户认证**：登录/注册系统，用于保存个人数据
- **文章管理**：增删改查、自动统计汉字数、图片上传、导入/导出 JSON
- **概念管理**：增删改查、分类/学科/章节管理、导入/导出 JSON
- **临床笔记管理**：增删改查、病机/治法/处方/备注字段、导入/导出 JSON
- **整体备份/恢复**：一键导出包含文章、概念、临床笔记的完整备份文件
- **WebDAV 同步**：支持坚果云、Nextcloud 等服务的全量数据上传下载
- **本地持久化**：所有数据自动保存到浏览器 localStorage
- **PWA 特性**：支持离线访问、可安装到桌面

## 技术栈

- **Vue 3** + **TypeScript** + **Vite**
- **Pinia**：状态管理
- **Vue Router**：路由管理
- **TailwindCSS**：样式框架
- **Lucide Vue Next**：图标库
- **webdav**：WebDAV 客户端
- **vite-plugin-pwa**：PWA 支持

## 运行方式

### 开发模式

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 构建部署

```bash
# 构建生产版本
npm run build

# 预览生产版本
npm run preview
```

## 目录结构

```
src/
├── main.ts              # 应用入口
├── App.vue              # 根组件
├── style.css            # 全局样式
├── router.ts           # 路由配置
├── types/
│   └── index.ts        # 类型定义
├── stores/             # Pinia 状态管理
│   ├── auth.ts         # 用户认证状态
│   ├── article.ts      # 文章状态
│   ├── concept.ts      # 概念状态
│   └── clinical.ts     # 临床笔记状态
├── services/           # 业务服务层
│   ├── article.ts      # 文章数据操作
│   ├── concept.ts      # 概念数据操作
│   ├── clinical.ts     # 临床笔记数据操作
│   ├── backup.ts       # 备份与恢复
│   └── webdav.ts       # WebDAV 同步
├── utils/              # 工具函数
│   └── imageCompression.ts  # 图片压缩
└── views/              # 页面组件
    ├── Auth/
    │   ├── Login.vue       # 登录页
    │   └── Register.vue    # 注册页
    ├── Home.vue        # 首页
    ├── article/
    │   └── ArticleList.vue # 文章列表
    ├── concept/
    │   └── ConceptList.vue # 概念列表
    ├── clinical/
    │   └── ClinicalList.vue # 临床笔记
    ├── Backup/
    │   └── Backup.vue       # 备份与恢复
    └── Settings.vue    # 设置页
```

## 数据同步

与 Windows 端和鸿蒙端共享相同的 JSON 备份格式，可通过 WebDAV 或文件导入/导出进行数据同步。

## 许可证

MIT License
