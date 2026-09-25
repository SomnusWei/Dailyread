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
- 📝 **在线考试（教师/管理员）**：「发起考试」上传**考卷**（必填）与**答案卷**（选填）交互式 HTML（自动提取内嵌 `exam_id` 建考试），设置作答时间范围与面向等级/指定账号；**标题选填，留空自动取考卷文件名（去 .html）**；未上传答案卷时该考试不显示答案卷入口、文件数按实际上传计；可删除考试（登录密码二次确认）；「成绩查询」按学生用户名/等级查看其所有相关考试的状态徽章（成绩 xx 分/未完成/超时作废）、得分、提交时间，并可打开该生考卷与答案卷
- 📝 **在线考试（学生）**：考试中心列出分发给自己且已开始的考试；窗口内未完成可开始作答，提交后原地批改并上报成绩；已交卷可查看**带本人作答与批改回显**的考卷（成绩卡 + 逐题对错/未答/简答自评），重做不计分；未获成绩不可看答案卷；截止未交自动「超时作废」（可练不计分）；整卷锁定防重复提交
- 🎓 **考试账号关联与回显**：学生作答上报自动携带学习中心账号（`student_username`，识别自 URL `?student=`/同源 `localStorage['lc_user']`），服务器归属优先级 = 卷显式账号 → 会话 Cookie(`lc_token`) → 卷内姓名，改名不影响成绩归属；「查看考卷」先经 `GET /api/learning/exams-detail` 取明细写同源 localStorage，再以 `?r=1` 打开由**题库 skill 生成卷的「成绩回显模式」**还原作答与批改

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
├── SKILL/                                   # 医学综合 skill（yixue-zonghe）
│   ├── SKILL.md                            # skill 路由与通用规则（含中西医双轨分流、动态专家发现、讲义体例路由）
│   ├── yixue-zonghe-skill.zip              # ★ 技能分发包（完整包，约 831MB；中医教材源书 PDF/EPUB 按 .gitignore 口径不入包，txt 已随包）
│   ├── 中医教材/                           # 724 部中医知识库（现代教材 + 古籍）
│   ├── 西医教材/                           # 西医教材（PDF 源 + 转写 txt，支持 PDF/DOCX/DOC/TXT 自动 OCR）
│   ├── 倪海厦体系/                         # 倪海厦经方体系（14 模块 + 1257 医案 + 蒸馏速查）
│   ├── 石学敏体系/                         # 石学敏针灸体系（醒脑开窍/手法量学/十二经病候 + 针灸全集分卷）
│   ├── 仓颉/                               # 蒸馏工具（教材/人物/视频课程 → 专家 Skill 认知蒸馏）
│   ├── 蒸馏产出/                           # 蒸馏生成的专家 perspective Skill（含 _inbox 工作区）
│   │   ├── 王洪图-内经-perspective/        #   A 类人物蒸馏（中医·内经学）
│   │   ├── 张廷模-中药学-perspective/      #   A 类人物蒸馏（中医·中药学）
│   │   ├── 刘忠保-生理学-perspective/      #   C 类视频课程蒸馏（西医·生理学）
│   │   ├── 邓中甲-perspective/             #   B 类教材蒸馏
│   │   ├── 娄绍昆-perspective/             #   A 类人物蒸馏（中医·经方方证辨证）
│   │   ├── 经方-perspective/               # ★ 主题专家·多源合成（八部中医内科著作）
│   │   └── 示范医家-perspective/           #   A 类人物蒸馏
│   ├── scripts/                            # 检索/提取/出题/同步/讲义转换脚本（--track 中医/西医 切换）
│   │   ├── search_textbooks.py             #   全库检索（中西医分流，按体系过滤蒸馏专家）
│   │   ├── build_exam_html.py              #   交互式试卷生成器（含 PWA 考试端适配）
│   │   ├── to_onenote.py                   #   讲义 HTML → OneNote 适配版（通用体例；--check/--check-only 自检）
│   │   ├── strip_timestamps.py             #   ★ 讲义时间戳清洗器（交付前必跑；兼容 span.ts／OneNote span／裸文本）
│   │   └── ...
│   ├── references/                         # 教材索引、关键词映射、病案/处方/出题规范
│   │   ├── onenote-html-spec.md            #   讲义 OneNote 适配 HTML 规范（通用体例）
│   │   ├── lecture-format-fangjixue.md     #   ★ 方剂学讲义体例规范（每方七层 + 五附录）
│   │   ├── lecture-format-physiology.md    #   ★ 生理学讲义体例规范（［目标］/［第N节］/［速查］）
│   │   ├── lecture-format-zhongyaoxue.md   #   ★ 中药学讲义体例规范（十节）
│   │   ├── lecture-format-neike.md         #   ★ 中医内科学讲义体例规范（六层 + 三专家卡 + 四附录）
│   │   ├── wanghongtu-integration.md       #   王洪图内经学体系运行时摘要
│   │   ├── zhangtingmo-integration.md      #   张廷模中药学体系运行时摘要
│   │   ├── liuzhongbao-integration.md      #   刘忠保生理学体系运行时摘要
│   │   ├── laoshaokun-integration.md       #   娄绍昆经方方证体系运行时摘要
│   │   ├── jingfang-integration.md         # ★ 经方专家库（多源合成）运行时摘要
│   │   ├── examples/                       #   ★ 体例蓝本（完整成品，讲义照它写）
│   │   └── ...
│   ├── templates/                          # 讲义 HTML 模板与样式
│   └── platform/                           # ★ 个人工作平台（本地 Web UI，零依赖）
│       ├── start.py                        # 后端服务（http.server + 20+ API）
│       ├── index.html                      # 单文件 SPA（概览/教材库/跨库检索/技能产物/专家体系/功能导航）
│       ├── start.bat                       # 双击启动器（浏览器版，默认 127.0.0.1:8770）
│       ├── desktop/                        # ★ Electron 壳（原生窗口版，免开浏览器）
│       │   ├── main.js                     # 主进程：定位技能根/Python → 拉起后端 → 开窗
│       │   ├── loading.html                # 启动动画
│       │   ├── package.json                # electron-builder 配置（portable 单文件）
│       │   └── build/icon.ico              # 应用图标
│       ├── extract_shixuemin.py            # 石师针灸全集 PDF 抽取（幂等）
│       └── verify_platform.py              # 端到端自检（43 项）
├── docs/                                   # 项目文档与教程
│   └── 考试作答指引/                        # 学习中心在线考试作答教程（tutorial.html + PDF + 流程截图）
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

### 2026-09-25

**两座新专家库（娄绍昆 · 经方）+ 八部中医内科教材入库 + 《中医内科学》讲义体例与蓝本：**

**一、娄绍昆专家库（A 类人物蒸馏）**
- 🧬 **新增** `蒸馏产出/娄绍昆-perspective/`：素材为娄绍昆著、娄莘杉整理《中医人生——一个老中医的经方奇缘》增订版（EPUB → 62 段 / **53.3 万汉字**）。产出 `SKILL.md`（55KB：8 信念 + 6 关键决策 + 6 栽跟头 + 5 内在矛盾 + **7 模型** + 3 推理示例 + 6 护栏 + Harness Engine）＋ 4 件调研件（451 条提取记录中的 77 条、98 条带出处的逐字引文、篇章地图）
- ✅ **质检 11/11**（女娲 6/6 + 仓颉 5/5，独立复跑确认）
- ⚠️ **引用核验发现并修掉 6 处偏差**：删 1 处伪引（「通过这些论述，张丰先生把我带进了腹证的世界。」原书无此句）、订正 4 处与原文不符（「一个人穷究…」原文为「**张三**穷究…」、「本书不是一般的回忆录」原文为「**一书**…」、「**读书**读着读着」原文无"读书"、景岳引文截断补足末句）；订正后严格核验 **101/118 = 85.6% 逐字命中**，余为「原文与『他说』插叙交错」的合法合并
- 🧭 **新增运行时摘要** `references/laoshaokun-integration.md`（能力匹配、归属规则、不得越界 8 条、素材局限）

**二、经方专家库（首个「主题专家·多源合成」）**
- 🧬 **新增** `蒸馏产出/经方-perspective/`：**八部著作合成**——秦伯未（谦斋）《中医处方学》《医学讲稿》《四大经典简释》、姚荷生《中医内科学评讲》、印会河《中医内科新论》、赵绍琴《内科学》、《实用中医内科学》第 2 版、《名老中医之路》（65 篇合集）
- 产出 `SKILL.md`（65KB：**7 模型**——抓主症定方／处方公式与审方四维／一切诊断先回到六经／脉舌色症不舍脉从症／分期分阶带停止条件／无证可辨则辨病论治／不掩瑕标证据强度 ＋ 6 组内在矛盾 + 12 条认知边界 + 3 推理示例 + 护栏 + Harness Engine）＋ 20 件调研件（**451 条**提取记录 / **364 条**逐字引文 / 8 份篇章地图 / 来源清单 / 合并版知识图谱）
- 🔖 **不是某一位医家**：人称用「我」但**每条主张点名归属**（谦斋／姚荷生／印会河／赵绍琴／教材／《名老中医之路》某篇），各家分歧**如实并列不调和**；并声明三处易错归属（孙其新编按≠秦伯未原文、赵绍琴书上篇治验按语多出弟子手笔、《名老中医之路》编者版本未能从文本确认）
- ✅ **质检 11/11**；**归属核对 31/31 = 100%**、逐字引文 106/116 = 91.4%（余为自撰术语与 OCR 讹字差异，无臆造）
- 🧭 **新增运行时摘要** `references/jingfang-integration.md`

**三、八部中医内科教材入库（`中医教材/` 716 → 724 部）**
- 📚 入库：名老中医之路（909 页）／印会河中医内科新论（419）／赵绍琴内科学（400）／谦斋四大经典简释（382）／中医内科学评讲（362）／谦斋中医处方学（329）／谦斋医学讲稿（233）＋《实用中医内科学(第2版)》（EPUB）
- 🔤 **7 部扫描件共 3,034 页走整页 OCR**，产出 txt 合计 **347 万字符**；EPUB 单行转 txt（159.5 万字符）——脚本不处理 epub，改由独立提取补齐
- 🐞 **修掉 OCR 管线一处缺陷**：扫描件原被「整页 OCR + 该页内嵌整图 OCR」识别**两遍**（实测重复长行占 **47.3%**，耗时亦翻倍）。对纯扫描书改用 `sync_new_materials.py --track 中医 --no-images-ocr`，重复率降至 **0.1%**，速度由 2.5 s/页提升到 **0.83 s/页**
- 🗂 索引已重建（**724 个 txt**，其中 7 个由 PDF 自动转写）；源书 PDF/EPUB 按 `.gitignore` 口径不入 git 与分发包

**四、《中医内科学》讲义体例 + 蓝本（第四套体例）**
- 🧭 **`SKILL.md` 讲义体例路由新增**：主题为中医内科学的**章或病证** → **中医内科学体例**；该体例**默认三专家并列**（倪海厦 · 娄绍昆 · 经方专家库），主题色固定 **`#014198`（RGB 1,65,152）**，章标题带 `［第N章］`／`［附录N］` 标签，目录**只列到章节两级**，附录固定四个
- 📐 **新增体例规范** `references/lecture-format-neike.md`：骨架（封面表 → 目录 → ［第N章］ → 章首概要 → 各节六层 → 四附录）＋ 4.4 节内固定栏目数量表（教材基线卡 8～9／临床联系卡 2／古籍摘要卡 1／记忆框架卡 1／高频考点·低频易混双栏 1／三专家卡各 1）＋ 4.5 三专家卡规格 ＋ 5.1 单档配色表 ＋ 专家标注边界 ＋ 12 条硬性规则
- 📄 **新增蓝本** `references/examples/中医内科学-肺系病证讲义_OneNote版样板.html`（44.1 万字符 / 588KB，《中医内科学》第五版第四章肺系病证八节全 + 四附录）；相对原讲义做了两处改造：**目录删去节下子项**（9 行 → 两级目录）、**主题色由青 `#0f6b6b` 改为 `#014198`**（10 个色值 / 1,246 处），语义卡色（专家卡琥珀、警示红、记忆紫、提示蓝、临床绿）一律保留
- 🃏 **向该讲义注入经方专家库** 13 张卡（章首总纲 1 + 八节各 1 + 附录四速查 4）+ 新增 ［附录四］经方专家库速查表四张（七模型／病证矩阵／原话精选／使用纪律与边界），并同步头部专家体系、目录、页脚与附录三「专家内容**三个**来源」
- ✅ **质检清单新增「中医内科学体例检查」19 项**；蓝本逐条自检通过（`padding-left:14px` 子项 0／六层各 8／三专家卡齐全／旧青系色 0／标签全配对／0 class）＋ `to_onenote.py --check-only` 全过；注入的 **57 条新增引文 57/57 = 100% 逐字命中**素材

**五、分发包与一致性**
- 📦 **重新打包** `SKILL/yixue-zonghe-skill.zip`：**1417 条目**（67 目录 + 1350 文件）/ **831.4MB** / UTF-8 文件名 / 完整性 OK；抽验蓝本、体例规范、两份接入摘要、两座新专家库、教材 txt 均与工作区一致
- 🔁 **安装版 ↔ 本地版逐文件核对：0 差异**（各 1338 个文件，含教材源文件）

### 2026-09-21

**学习中心「发起考试」标题与答案卷改选填（已部署）+ 医学综合 skill 两项调整：**

**一、学习中心 · 考试发布（服务端，已上线）**
- ✏️ **标题改为选填**：表单新增「考试标题（选填，≤128 字）」输入框；**留空时服务端取考卷文件名（去 `.html` 后缀）**，保留原有 latin1→UTF-8 文件名乱码纠正；前端仅在标题非空时才提交 `title` 字段
- 📄 **答案卷改为选填**：不再要求「考卷 + 答题卡」成对上传，只传考卷即可发布；未上传时 `answer_filename` 存 `NULL`（`lc_exams.answer_filename` 由 `NOT NULL` 改 `NULL`，含启动自动迁移 `MODIFY COLUMN`，老数据不受影响）；答案卷的 `exam_id` 一致性校验改为**仅在提供了答案卷时**执行
- 🖥 **前端兼容**：考试列表/成绩查询在无答案卷时不渲染「答案卷」入口，`文件：N 个` 按实际上传计；`sw.js` 缓存 `lc-mission-v16 → v17`（`/center/app.html`、`/center/js/app.js` 在预缓存清单内，不升版会继续命中旧表单）
- ✅ **部署核验**：5 个文件 scp 上传后 MD5 与服务端逐一一致；覆盖前备份至 `/opt/dailyread-server/backups/deploy-20260921-210547/`；`systemctl restart dailyread-server` 后日志出现 `migration: lc_exams.answer_filename_nullable added OK`；DB 列实测 `varchar(255) YES NULL`；线上 `app.html` 含 `examTitle`、答案卷 `required` 残留 0、`sw.js` 为 v17、`/health` 200

**二、医学综合 skill · 中药讲义配色随药性变动**
- 🎨 **新增「5.1 药性配色」**（`references/lecture-format-zhongyaoxue.md`）：讲义色调由该药**四气**决定——寒凉走冷色（寒 `#23557d` 靛蓝／凉 `#1a6f69` 青碧）、温热走暖色（温 `#ab5f13` 琥珀／热 `#b03a26` 朱）、平性走中性棕金 `#8a5b00`；每档给出**11 个位置**的完整十六进制（主题色/主题深色/教材基线卡三色/小结框两色/隔行底纹/专家卡四色/引文块字色）
- 📐 **定档规则**：单味药按教材【药性】四气（大寒→寒、微寒→凉、微温→温、大热→热、平→平）；整章多味药按**节**主导药性；节内寒热混杂退化为**平**；**全篇一档到底**不得混档
- 🔒 **语义卡色固定不变**（警示 `#a83232`／记忆 `#6b4fbb`／提示 `#2a6099`／临床 `#1a6b3c`／大字块 `#3b2675`）：冷档提示卡是蓝、暖档主题色与警示红同属暖区，靠徽标文字与各自底纹区分，不为迁就配色改语义色
- 📄 **蓝本改造**：`references/examples/中药学-麻黄讲义_OneNote版样板.html`（麻黄为**温性**药）整体改到温档（`#8a5b00→#ab5f13` 等 11 处色值共 245 次替换），`to_onenote.py --check-only` 自检通过（0 class／0 残留／标签全平衡）
- ✅ **质检新增第 10 条「配色与药性一致」**：主题族与专家族色值须取自同一档，不得混档、不得留用他档残留

**三、医学综合 skill · 出题答案卷默认不出**
- 🔧 **`scripts/build_exam_html.py` 新增 `--with-answers`（默认关）**：**默认只产出交互式试卷 `{卷名}.html`**，加参数才额外出 `{卷名}_答案卷.html`；产出日志在未生成时明确提示「如需请加 --with-answers」
- 📘 **`SKILL.md` 功能六与 `references/quiz-guide.md` 同步**：标准交付物改为「默认只交付交互式试卷」，流程第 ④ 步改为「生成试卷（答案卷按需）」，生成命令／产出文件数（默认 1 个、加参数 2 个、要 PDF 3 个）／质检项／「默认交付」句一并更新；平台工作台提示改为「上传考卷即可分发（标题可留空取文件名，答案卷选填）」
- 🧪 **回归验证**：同一 2 题测试卷，**不加参数**只出 1 个文件（35,988 B）、**加 `--with-answers`** 出 2 个（试卷同为 35,988 B ＋答案卷 2,718 B）——两种模式下试卷字节数一致，说明开关只影响答案卷产出
- ℹ️ 说明：题库 JSON 中的 `answer/answers/reference` **仍照写**（交互试卷靠它在线判分与 `?r=1` 回显），与「是否导出答案卷」是两件事

### 2026-09-20

**医学综合 skill：新增第四位蒸馏专家「王洪图·内经学」+ 以安装版为准全量对齐：**
- 🧠 **新增「王洪图·内经学」专家体系**（`蒸馏产出/王洪图-内经-perspective/`）：A 类人物蒸馏，素材为四部一手文本约 **157 万字符**——《王洪图内经讲稿》80 讲授课实录（505,632 字符）、《王洪图内经临证发挥》（243,574 字符，扫描件整页 OCR 369 页）、《黄帝内经素问白话解》与《灵枢白话解》主编本（476,752 + 343,919 字符，仅用于篇目图谱）。产出 7 条信念 + 6 个心智模型（以经解经／功能·整体·变化三角度／中焦气机枢纽→神志病从脾胃转枢／引经入证／多解并存两把尺子／理论—临床—实验三层验证）+ 2 个推理示例 + 6 条反模式护栏 + Harness Engine
- ✅ **质检 11/11 通过**（女娲 6/6 + 仓颉 5/5）；关键引用回搜素材原文 **23/23 命中**，无臆造
- 🔗 **新增专家接入摘要** `references/wanghongtu-integration.md`：中医学习／讲义／病案／出题默认融入；针灸限经络理论、处方讲解限经旨立法（实操量学归石师、君臣佐使归邓中甲）；西医功能不调用
- 📚 **以安装版为准全量对齐**（含教材）：`SKILL.md` 采用安装版 09-19 22:04 版（技能包格式，含 frontmatter）；并补齐此前仅存在于安装目录的 `蒸馏产出/张廷模-中药学-perspective/`、`references/zhangtingmo-integration.md`、`references/lecture-format-zhongyaoxue.md`、`references/examples/中药学-麻黄讲义_OneNote版样板.html`、`中医教材/中药功效学(张廷模).txt` 与《中药学讲稿(张廷模)-精校》txt/doc、王洪图专家全套与 `_inbox/王洪图-内经/材料/`。对齐后 `中医教材` 716 部 txt（+《中药学讲稿》doc）、`西医教材` 11 PDF + 11 txt，**逐文件校验两侧差异为 0**（排除 node_modules / dist / `__pycache__`）
- 📄 **同步 6 个安装版较新的文件**：`quality-checklist.md`（新增中药学体例检查）、`quiz-guide.md`（**卷面洁净原则**：出题大纲、难度与考试场景标记一律不上卷面）、`build_exam_html.py`（生成时清除题干难度标记）、`to_onenote.py`（`<img>` 直通与图注）、`text_utils.py`（Word 退出 RPC 偶发失败不再丢弃已转存内容）、`textbook-index.md`（重建索引，716 个文本文件）
- 📦 **重新打包技能分发包** `SKILL/yixue-zonghe-skill.zip`（**1367 条目** = 59 目录 + 1308 文件 / **826MB**，UTF-8 文件名，解压根目录 `yixue-zonghe/`）

### 2026-09-18

**医学综合 skill 建立「讲义体例体系」（方剂学／生理学专用体例）+ 两份验证讲义：**
- 🧭 **新增讲义体例路由**（`SKILL.md` 功能二）：动手前先按主题判定体例，照体例蓝本写——方剂学（按「剂」成章）→ **方剂学体例**；生理学（按教材章）→ **生理学体例**；其他主题 → 通用体例。命中前两者时**直接按蓝本的原生形态编写，不再经 `to_onenote.py` 转换**（实测再转一次会丢约 45% 底纹、`▍` 前缀重复叠加、并插入一张空目录表）
- 📐 **新增两份体例规范**：`references/lecture-format-fangjixue.md`（三篇骨架 + **每方七层**：① 组成用法 ② 功用主治 ③ 证治机理 ④ 配伍结构 ⑤ 剂量使用讲解（原方—教材—倪师临床）⑥ 附方 ⑦ 运用与鉴别；+ 五个附录含中药小讲义与速查表）、`references/lecture-format-physiology.md`（三段式：`［目标］` / `［第N节］` / `［速查］`，含专家口诀汇总表与章末思考题）
- 📄 **新增两份体例蓝本**（`references/examples/`，完整成品）：`方剂学-泻下剂讲义_OneNote版样板.html`（426.7KB）、`生理学-细胞的基本功能讲义_OneNote版样板.html`（312.8KB）。生理学蓝本入库前按时间戳规则处理：193 处 `P## [hh:mm:ss]` → 「刘忠保·第 N 讲」、12 处 `P02–P10` → 「第 2–10 讲」（`HSP90`/`HSP70` 等正常文本未误伤）
- 🔧 **`scripts/to_onenote.py` 新增 `--check-only FILE`**：对已成型的 OneNote 原生形态交付物执行与 `--check` 完全同一套自检（6 项残留 + 12 类标签配对）
- ✅ **质检清单新增「体例检查」** 两组共 15 项（`references/quality-checklist.md`）
- 📚 **验证产出两份完整讲义**（`讲义输出/`，已加入 `.gitignore`）：《方剂学》和解剂（**439.4KB / 168 表 / 17 方**：7 正方 + 8 附方 + 2 附论；附录含中药小讲义 37 味、方剂速查表、三列剂量对照表、专家边界声明）、《生理学》第三章 血液（**302.7KB / 208 表**：4 节 + 5 张速查表含刘忠保口诀 20 条 + 章末思考题）。两份均通过 6 项残留 + 标签配对自检，**全文 0 时间戳**
- 🐛 **修正 `蒸馏产出/刘忠保-生理学-perspective/references/research/04-knowledge-map.md`**：原「章节总表」的**集号区段自「细胞的基本功能」起整体错位**——同一 73 集被切成错误边界（血液误标 P13–P19、循环误标 P20–P33），曾导致《生理学·血液》讲义误标素材范围。现按 `transcripts_fixed/` 实际转写稿文件名**重定章界**（血液实为 P11–P15、循环 P16–P24、呼吸 P25–P31 …合计 73 集连续无重叠），并以 `summary.csv` 重算时长与字数（67.3 h / 1,212,615 字）；12 章「分集」行全部纠正，6 个抽样条目错档的章加「信号条目说明」如实标注
- 🧹 **删除重复安装副本** `~/.workbuddy/skills/yixue-zonghe`（09-15 旧版，866 文件，缺 `platform/`、OneNote 交付链路、刘忠保专家与全部新规则），仅保留 `.trae-cn/skills/` 一份，消除双副本歧义
- ⚠️ **记录一处既有缺陷（尚未修复）**：`templates/lecture-template.html` 与 `to_onenote.py` 不匹配——其 `<h2>` 缺 `class="sec"`（脚本对该情形直接返回空，实测转换后 **h2 数 = 0，章节标题全丢**），目录容器用 `div.toc` 而脚本只识别 `div.side`（目录表为空）。影响：走通用体例的其他主题讲义会缺章节标题与目录
- 🧽 **并入时间戳清洗器 `scripts/strip_timestamps.py`**：清洗讲义中的 `P## [hh:mm:ss]` 时间戳，兼容三种形态（网页版 `span.ts`／OneNote 版内联样式 span／裸文本），并清掉删除后遗留的多余空白、改写因此变成残句的说明文字；支持 `--in/--out/--inplace/--dry-run/--check`，**幂等**可重复跑
- 🐛 **修复该工具两处漏删**：① 同一 span 内并列多个时间戳（如 `P03 [00:57:19–00:59:53] / P04 [00:04:28–00:05:05]`）时原正则只匹配首个、随后要求紧跟 `</span>` 不成立 → 整段被漏删；② 自检未覆盖无讲次前缀的续段。实测对含 192 处时间戳的原始样板：清除数 181 → **189**，自检由「残留 13 处 + 底色 8 处」变为**全 0**
- 🧹 **清洗两份蓝本残留**（早先手工去时间戳不彻底）：生理学蓝本尚有 3 处无 `P##` 前缀的续段时间戳（如 `刘忠保·第 9 讲 / [00:39:38–00:42:15]` 的后半段）、8 处时间戳专属底色 `#f6e7cd`、2 处声明「引用带 `P## [hh:mm:ss]` 出处」的记法示例；均已清除，表格数不变（327）、标签配对平衡、再跑工具零改动
- 📌 **规范同步引用该工具**：`SKILL.md` 的时间戳规则补充「两类易漏形态」（无前缀续段、`P## [hh:mm:ss]` 记法示例）与清洗命令；两份体例规范的硬性规则①与质检节、`quality-checklist.md` 的专家内容合规项均已加入

### 2026-09-17

**医学综合 skill：新增第三位蒸馏专家 + 讲义交付改为 OneNote + 中西医双轨分流：**
- 🧠 **新增「刘忠保·生理学」专家体系**（`蒸馏产出/刘忠保-生理学-perspective/`）：仓颉在 A 类人物、B 类教材之外新开的 **C 类 · 视频课程蒸馏**——从课程视频转写稿中提炼认知上下文（体系定位、跨章串联框架、"不考/不要求"边界、先记后理解的教学法）。素材工作区 `蒸馏产出/_inbox/刘忠保-生理学/`（转写稿 raw/fixed、术语表、日志、manifest 等 391 文件，音频已剔除）
- 📄 **讲义交付格式由 PDF 改为 OneNote 适配 HTML**：新增 `scripts/to_onenote.py`（class 驱动网页版 → 零 class、字号一律 pt、侧栏目录转文内目录表格、渐变封面转 bgcolor 表格、卡片转双格表格、`::before/::after` 引号转实体字符；带 `--check` 自检）与 `references/onenote-html-spec.md`（规范：为什么 / 转成什么样 / 怎么验收）；SKILL.md 新增「**交付格式铁律**」（默认 OneNote HTML、**不输出 PDF**、网页底稿保留、转换必须走脚本、转换后必检）；讲义流程第 ⑤ 步由「PDF 导出」改为「OneNote 适配转换」；`quality-checklist.md` 新增「OneNote 版专属检查」12 项（无 class／无 CSS 变量／无渐变／无 sticky-fixed／无伪元素／无 px 字号／标签配对／结构统计一致／内容零丢失／无新增内容／文内目录非空／全角空格 U+3000 未折叠）
- 🔀 **专家体系统一为中西医双轨分流**：`SKILL.md` 的「中医功能执行前置」升级为「**功能执行前置**」，专家池分【中医专家】/【西医专家】/【通用·综合】，并明确「**体系不混用**」；`search_textbooks.py` 新增 `_expert_track()` 按 SKILL.md 内容判定蒸馏专家体系，**西医检索默认也跨库**（西医教材 + 蒸馏产出中的西医专家，不再混入倪师/石师经方与针灸内容）；`_inbox/` 与下划线临时文件不参与检索；检索结果显示名带来源前缀（`倪师/`、`石师/`、`蒸馏/<专家名>/`）便于溯源标注
- 📚 **新增题库** `scripts/exam_jiewen.json`：《方剂学·辛温解表剂及相关中药 专题试卷》
- 🔗 **新增专家接入摘要** `references/liuzhongbao-integration.md`（刘忠保生理学体系运行时索引）
- 📦 **新增技能完整分发包** `SKILL/yixue-zonghe-skill.zip`（1280 文件 / 821MB，UTF-8 文件名，解压根目录 `yixue-zonghe/`）

### 2026-09-15

**医学综合 skill 工作台新增「Electron 桌面版」单文件 exe：**
- 🖥 **`platform/desktop/` Electron 壳**：单文件 portable exe（**95.1MB**），双击即用，**不再需要手动开浏览器**。启动时自动定位技能目录与 Python、选空闲端口拉起 `platform/start.py` 后端，待 `/api/overview` 就绪后在原生窗口加载界面（启动期显示内嵌 loading 动画）
- 🧭 **零配置自动探测**：技能目录按 `YIXUE_SKILL_ROOT` → `config.json` 记录 → `~/.workbuddy/skills/yixue-zonghe` → `~/.trae-cn/skills/yixue-zonghe` → 可执行文件上级逐层查找，命中即用并写入 `%APPDATA%\医学综合工作台\config.json`；全部未命中才弹窗选择（选一次即记住）
- 🐍 **Python 探测**：`YIXUE_PYTHON` → `config.json` → workbuddy 默认解释器 → 技能包内 `.venv` → PATH
- 🔒 **退出即回收**：关闭窗口以 `taskkill /T /F` 结束后端进程树；异常退出写 `backend.log` 便于排查
- 📋 **精简菜单**（Alt 唤出）：视图（重新加载/开发者工具/缩放/全屏）、帮助（打开技能目录/打开数据目录/关于）
- 🎨 **应用图标**：墨绿圆角 + 「医」字，多尺寸 ICO（16→256）
- 🐛 **修复 `start.bat` 双击闪退**：根因是 LF 换行 + 中文多字节字符导致 cmd.exe 解析时字节偏移错位，启动行被截断成 `'HON~dp0start.py"...'` 而从未执行 Python。改为 **CRLF + 纯 ASCII** 并加 `.gitattributes`（`*.bat text eol=crlf`）；同时加固为三级 Python 探测 + 任何分支都 `pause` 停留
- ✅ **实测**：exe 双击启动 → 6s 后端就绪、窗口标题为应用界面、六库统计正确；关闭后 python 与 Electron 残留均为 0；无环境变量/无配置的首次启动可自动探测技能目录

**医学综合 skill 新增「个人工作平台」（本地 Web UI）：**
- 🖥 **新增 `SKILL/platform/` 零依赖本地工作台**：`start.bat` 双击启动（默认 `127.0.0.1:8770`），仅用 Python 标准库 `http.server`，不装 Flask/FastAPI；后端 `start.py` 提供 20+ API，前端 `index.html` 为单文件 SPA（6 个页面）
- 📚 **教材库管理页**：中医/西医体系切换、类目筛选、文件名搜索、分页浏览；拖拽上传 `.pdf/.docx/.doc/.txt`（≤500MB）；一键「同步解析」（PDF 文本层 + 扫描页 OCR + 内嵌图片 OCR，长任务后台执行并轮询进度）；「重建索引」刷新 `textbook-index*.md`；文本预览（自动识别 GB18030）与软删除（回收至 `platform/.trash/`）
- 🔍 **跨库检索页**：关键词（支持逗号分隔多词）+ 体系 + 来源（跨库/仅教材/倪师/石师/蒸馏产出）+ 类目 + 上下文行数 → 文件卡片按命中数降序、命中处高亮；命中文件过多时默认展开前 50 个
- ★ **蒸馏入口（专家体系页）**：填蒸馏类型（A 人物 / B 教材）、对象名、聚焦方向，拖拽上传素材 → 平台落盘 `蒸馏产出/_inbox/<对象名>/` 并自动生成 `DISTILL_PROMPT.md` **指令卡**（含仓颉 7 步流程、产出路径、质检要求，文本素材 ≤50KB 自动内联原文）
- 🧠 **蒸馏闭环（技能产物页）**：一键「查看/复制指令卡」→ TRAE 执行蒸馏 → 「检测产物」→「质检」（`quality_check.py` 11 项，未达 11/11 拒绝安装）→「安装到蒸馏产出」（自动重命名 `<对象名>-perspective/` 并清理指令卡与素材）；任务状态机 `pending → produced → quality_ok → 已安装`
- 📦 **导入已完成归档**：已有 perspective 的 `.zip` 经「导入已完成归档」解压到 `_inbox/_import/`（含 zip-slip 防护）供质检与安装
- 🪡 **石学敏针灸全集抽取**：`extract_shixuemin.py`（幂等）按 100 页分卷输出 11 卷 + `全文.txt` + `00-目录.md`，专家体系页在未抽取时显示「抽取全文」按钮
- 🔒 **安全约束**：路径穿越防护（`safe_join`）、上传/删除白名单根目录、文件名清理与 Windows 保留名检查、扩展名白名单、大小上限、受保护文件（`SKILL.md` 等）禁删、删除类操作二次确认
- ✅ **验证**：`verify_platform.py` 端到端自检 **43/43 通过**（环境/依赖/路径/纯函数/9 个 API/蒸馏任务闭环）；浏览器实测 6 个页面渲染正常、无控制台错误，跨库检索「桂枝汤」命中 388 个文件、5271 处高亮

**医学综合 skill（yixue-zonghe）再次升级——四层知识库 + 专家体系：**
- 🔄 **skill 整合**：合并旧的 `zhongyi-zonghe` 和 `yixue-zonghe` 两个 skill 为单一 `yixue-zonghe` skill，清除旧 skill 安装
- 📚 **四层知识库架构**：教材基线库（711 部中医教材 + 西医教材）→ 专家特化库固定（倪海厦经方体系 14 模块 + 1257 医案 / 石学敏针灸体系醒脑开窍 + 手法量学）→ 专家特化库动态（仓颉蒸馏产出）→ 工具层（仓颉蒸馏工具）
- 🧠 **倪海厦经方体系**：14 模块 + 1257 例结构化医案 + 6 蒸馏速查 + 表达 DNA，默认融入五大中医功能（学习/讲义/病案/针灸/处方），可选启用倪师医案命题规范
- 🌿 **石学敏针灸体系**：《石学敏针灸全集》1071 页 + 醒脑开窍/手法量学/十二经病候新解认知上下文
- 🔧 **仓颉蒸馏工具**：7 步蒸馏流程，对教材进行认知蒸馏生成可复用专家 Skill，持续扩展知识库
- ✅ **PWA 考试适配验证**：出题脚本 `build_exam_html.py` 与 PWA 考试系统完整对接验证通过——成绩上报（`/api/exam/submit` + sendBeacon/fetch keepalive/localStorage 三重保障）、学习中心账号识别（`?student=`/`lc_user`）、成绩回显（`?r=1` + `lc_exam_review:` localStorage）、exam_id 三级写入与服务器三级提取匹配

### 2026-09-14

**Windows 端（文章与概念管理器）：**
- 🐛 **修复同步后卡死 30+ 秒**：根因是 `refresh_table()` 在已有 315 行数据的表格上逐个 `setItem` 替换旧 item，Qt 内部逐个销毁旧 item + 更新模型索引，即使禁用重绘也无法避免 O(n) 模型更新开销，每行 ~110ms、整体 30+ 秒。修复方案：填充前先 `setRowCount(0)` 一次性清空所有行，再 `setRowCount(len)` 重建空行，使 `setItem` 退化为往空行插入（与首次启动一致）。修复后同步拉取后 `refresh_table` 从 33619ms 降至 68ms，提升 494 倍

### 2026-09-12

**医学综合 skill（yixue-zonghe）全面升级——中西医双轨知识库：**
- 🔄 **skill 重命名**：`zhongyi-zonghe` → `yixue-zonghe`，从纯中医扩展为中西医双轨综合性医学技能，六大功能（医学学习、讲义制作、病案/病例分析、针灸、中药/西药处方讲解、模拟题出题）均支持中医与西医双体系，通过关键词「中医」/「西医」区分
- 📚 **教材目录重构**：`SKILL/教材/` → `SKILL/中医教材/`（712 部：10 现代教材 + 702 古籍）+ `SKILL/西医教材/`（用户自行添加）；新增《邓中甲方剂学讲稿》（成都中医药大学邓中甲教授主讲，完整方剂学体系）
- 📄 **多格式教材导入**：新增 `sync_new_materials.py`，支持 PDF / DOCX / DOC / TXT 自动转换为可检索 txt；PDF 支持文本层提取 + 扫描页 OCR + **内嵌图片 OCR**（图表/解剖图）；`--track 中医/西医` 指定归档体系，`--from` 批量导入，`--no-images-ocr` 跳过图片 OCR
- 🔍 **检索脚本增强**：`search_textbooks.py` / `extract_content.py` / `build_textbook_index.py` 均新增 `--track 中医/西医` 参数切换教材目录；`text_utils.py` 新增统一入口 `extract_file_text()` 按扩展名自动分发（PDF→PyMuPDF+RapidOCR，DOCX→python-docx，DOC→Word COM，TXT→编码检测）
- 📋 **西医关键词映射**：`references/keyword-mapping.md` 新增西医疾病/系统/药物关键词表，支持西医教材自动分类索引

### 2026-09-09

**数据备份（服务器 → 本地/NAS 全链路）：**
- 🆕 **服务器定时自动出包**：`dailyread-server/scripts/backup.sh` 每日 03:10 经 cron 执行——`mysqldump --single-transaction` 在线热备全库（含建库语句，不锁表）+ `public/uploads/schema.sql` 站点数据打包，产物目录 `backups/backup-<时间>/`（`db-*.sql`、`site-*.tar.gz`、`sha256.txt`、`backup.log`）；按目录名时间戳自动清理超过 30 天的历史包。数据库凭据经 `scripts/db_env.js`（dotenv）从应用 `.env` 读取，脚本不硬编码、不回显密码
- 🆕 **Windows 备份助手 App**（`Dailyread_win_backup_assistant/`，已打包 `每日阅读备份助手.exe`）：PyQt6 + paramiko(SFTP) 从部署服务器拉取备份包到**本地目录或 NAS 共享（`\\NAS\…`）**。提供：① 手动「立即备份（远程出包+拉取）」与「仅拉取最新包」；② 三页界面（立即备份/历史备份/定期自动）；③ 定期自动备份——一键注册 **Windows 计划任务**（每天或每周指定时间，可选“错过开机尽快补跑”）；④ 下载后自动 **SHA-256 完整性校验**（存在且校验一致的包自动跳过）；⑤ 按保留天数清理过期备份；⑥ 月度日志文件 + 界面内“恢复指引”（数据库导入与站点解压步骤）。EXE 静默模式 `--auto` 供计划任务调用

### 2026-09-05

**学习中心 · 在线考试 + 中医综合 skill 试卷生成端到端对接：**
- 🆕 **考试发布/管理/成绩（教师·管理员）**：发起考试需成对上传「考卷 + 答案卷」交互式 HTML（自动提取内嵌 `exam_id`，可校验两卷一致），设置起止时间、面向等级与指定账号；**标题不再手工填写**，由服务器按考卷上传文件名（去 `.html`）兜底生成；管理页可打开考卷/答案卷预览与删除（密码二次确认）；新增考试列表/成绩查询（按学生用户名或等级，展示每场考试的状态徽章/得分/提交时间/文件）
- 🆕 **考试中心（学生）**：列出分发给本人且已开始的考试；未完成窗口内作答提交即出成绩；**已交卷可打开带作答与批改回显的考卷**（还原勾选/填空/简答、整卷锁定、成绩卡、逐题对错与正确答案/未答/简答自评），重做不计分；答案卷仅交卷后可看；截止未交自动超时作废（仅可练不计分）
- 🔗 **成绩与账号强关联**：上报归属 = 试卷显式 `student_username` → 学习中心会话 Cookie(`lc_token`) → 卷内姓名；学生改名不影响归属，教师/管理员可按账号查回
- 🧩 **Skill 试卷生成端适配**（`SKILL/`，build_exam_html.py）：生成卷内置账号识别（`?student=/?u=` → 同源 `localStorage['lc_user']`）预填姓名并随上报附 `student_username`；新增**成绩回显模式**（`?r=1` + 同源 `localStorage['lc_exam_review:<exam_id>']`：还原作答、整卷锁定、成绩卡、逐题批改标注）；上传时标题缺省取文件名；详见 SKILL.md「功能六 · PWA 学习中心部署」小节
- 🧪 交付验证：用该 skill 生成《中药学·解表药》150 题专项卷（单选120/多选30，含性味归经/相似药鉴别/临床应用/药物配对/功效用法用量注意事项配比），完成发布→作答→成绩回显→教师查分的端到端验收；`GET /api/learning/exams-detail` 可返回该生完整 `answers[]`
- 🔧 修复：教师/管理员成绩查询前端与后端字段结构不一致（读 `data.rows`、`student_nickname/exam_title`、补 `answer` 文件字段）导致成绩始终查询不到

**医学综合 skill（yixue-zonghe）出题/安装增强：**
- 🎲 **选择题选项默认随机打乱**：避免正确答案位置集中（如几乎全为 A）；`--no-shuffle` 保留原序、`--seed N` 固定顺序复现
- 🏷 **主观题关键词自动批改**：short 题配置 `keywords` 后按作答是否命中**参考答案实质内容**逐条给分（如医案分析：辨病答出"肺胀"、代表方答出"葶苈大枣泻肺汤"才得分，命中项累加、封顶本题分值）；同义词用 `words` 数组；逐条命中反馈，作答前不显示命中词（防泄题）
- ✂️ **文本归一化增强**：判分前统一全半角与大小写并清除各类中英文标点，关键词条含顿逗号等连接符也能正确识别
- 📐 **出题规范补充**：题干（stem）只放病案与作答要求；病案出处、辨治依据（如"按《中医内科学》辨治"）等一律放 `reference`/`explanation`，作答前对考生不可见
- 📦 **结构/安装**：skill 根目录为仓库 `SKILL/`；内置 712 部中医教材（10 现代教材 + 702 古籍，含邓中甲方剂学讲稿），置于 `中医教材/`；西医教材目录 `西医教材/` 待用户自行添加（支持 PDF/DOCX/DOC/TXT 自动 OCR 转换）；检索/提取脚本通过 `--track 中医/西医` 切换，也可 `--textbook-dir` 覆盖

**Windows 端（文章与概念管理器）：**
- 📖 **「预览阅读」入口移入编辑界面**：编辑文章对话框左下角新增“预览阅读”按钮（快捷键 **Alt+Q**），可**实时预览当前编辑内容（未保存亦可）**——按鸿蒙端阅读界面渲染：白底、标题粗体 fontSize+6、“N 字”、`##…##` 注解红色小号、`**…**` 加粗、`==…==` 黄色高亮背景、行距≈字号×1.8、WebP 图（<500px 原尺寸 / ≥500px 等宽自适应）、A-/A+ 调节字号（12–60，可随时重渲染）；仅只读预览，不打卡、不写库

**鸿蒙端（阅读器）：**
- 🎨 **`==…==` 黄色高亮**：Reader（每日阅读）、RandomRead（随心阅读）、EarPracticeReader（磨耳跟背）三处正文解析统一支持第三种行内标记，与 `##…##`（红字小号注解）、`**…**`（加粗）状态机同构；`==内容==` 片段以 `textBackgroundStyle` 渲染黄色背景（#FFEB3B、圆角 2），其余片段透明。Win 端「预览阅读」已同步解析该语法，保证两端渲染一致

**PWA（每日阅读）：**
- 🌐 **阅读正文行内标记渲染**：`center/dr` 阅读页支持 `##…##`（红字小号）、`**…**`（加粗）、`==…==`（黄色高亮）三种语法，纯文本 `content` 经转义后按与鸿蒙同一状态机语义渲染；已含 HTML 的 `contentHtml` 原样显示不二次解析。SW 缓存升至 `lc-mission-v14`

- 🔀 **三种样式可相互嵌套组合**（如 `==**…**…==`、`##**…**…##`）：鸿蒙（Reader/RandomRead/EarPracticeReader）、Win「预览阅读」、PWA 每日阅读三端同步改为**栈式解析**，红小字/加粗/黄底等样式属性按片段叠加渲染，支持任意嵌套；未闭合标记保留样式到结尾，非标准交错写法按栈规则处理
- 🔊 **每日阅读设置页新增「自动播放 / 循环播放」开关**（PWA center/dr）：仅本机 localStorage 保存；自动播放进入含音频文章即尝试朗读（移动端被浏览器拦截则需点一次播放），循环播放与阅读页音频条循环开关同步并即时生效。SW 缓存 v16

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
