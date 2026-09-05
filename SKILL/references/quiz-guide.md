# 模拟题出题指南

> 供「模拟题出题」功能使用。支持执业医师考试、考研、跟读自测三类场景；默认交付**可交互 HTML 试卷（自动批改）**，答案卷 PDF 为可选项。

---

## 〇、标准交付物

1. **交互式 HTML 试卷**（`build_exam_html.py` 生成，**必出**）——顶部填学生姓名，按题型作答，提交后原地批改并显示成绩卡
2. **题目+答案 PDF**（答案卷 HTML 转 PDF，**可选**）——含每题答案、解析、出处；仅当用户明确要求 PDF（或明确要打印版）时才生成，默认只交付答案卷 HTML 即可

---

## 一、出题流程（五步）

```
①确认需求（大纲/题数/总分/场景/难度）→ ②知识库取材 → ③命题 → ④生成试卷与答案卷 → ⑤质量自检
```

### 第 1 步：确认需求（三项必问，缺一不可）

用户要求出题时，**必须先确认以下三项**（用户未主动给出时追问）：

| 必问项 | 说明 | 默认值（用户说"随便"时） |
|--------|------|------------------------|
| **出题大纲** | 科目+考点范围（如"胸痹的病机与分型论治"） | — 必须问 |
| **题数** | 总题数及题型分配建议 | 10 题 |
| **总分** | 总分值（各题分值合计必须等于总分） | 100 分 |

可选确认项：场景（执业医师/考研/自测）、难度分布（默认 3:5:2）、考试时长、是否含主观题。

### 第 2 步：知识库取材

**原则：题干与答案必须有知识库出处，禁止凭空命题。**

```bash
# 科目取材（现代教材为命题主源）
python scripts/search_textbooks.py --keyword "{考点关键词}" --files "中医内科学.txt"
# 经典原文题取材
python scripts/search_textbooks.py --keyword "{条文关键词}" --category 伤寒论,金匮要略
# 针灸题取材
python scripts/search_textbooks.py --keyword "{穴名/病名}" --category 针灸推拿
```

### 第 3 步：命题（写入 exam.json）

命题完成后，按以下 schema 构造 `exam.json`（这是 `build_exam_html.py` 的输入）：

```json
{
  "title": "中医基础理论模拟试卷",
  "outline": "覆盖：阴阳五行、脏腑、气血津液",
  "total_score": 100,
  "duration": "60分钟",
  "questions": [
    {"type": "single", "score": 2, "stem": "题干",
     "options": ["A. …", "B. …", "C. …", "D. …", "E. …"],
     "answer": 0,
     "explanation": "解析（含干扰项分析）", "source": "《中医基础理论》第一章"},

    {"type": "multiple", "score": 2, "stem": "…",
     "options": ["…"], "answers": [0, 2],
     "explanation": "…", "source": "…"},

    {"type": "fill", "score": 2, "stem": "题干含____",
     "answers": ["可接受的答案1", "别名"],
     "explanation": "…", "source": "…"},

    // 医案分析简答题 + 关键词自动批改示例（命中词 = 参考答案的实质内容/术语，而非题干要求词“辨病/代表方”本身）
    {"type": "short", "score": 5, "stem": "医案分析：…（要求答出辨病、辨证、核心病机、治法、代表方）",
     "reference": "辨病：感冒（太阳伤寒表实证）；辨证：风寒束表证；核心病机：风寒外束、肺气失宣；治法：发汗解表、宣肺平喘；代表方：麻黄汤。",
     "key_points": ["辨病准确", "辨证准确", "病机准确", "治法一致", "方药正确"],
     "keywords": [
       {"words": ["感冒", "太阳伤寒"], "score": 1},        // 辨病：答出其一即命中
       {"words": ["风寒束表", "表实证"], "score": 1},      // 辨证
       {"words": ["风寒外束", "肺气失宣"], "score": 1},    // 核心病机
       {"words": ["发汗解表", "宣肺平喘"], "score": 1},    // 治法
       {"word": "麻黄汤", "score": 1}],                     // 代表方
     "explanation": "…", "source": "…"}
  ]
}
```

**schema 硬性要求：**
- `total_score` 必须 = 所有题目 `score` 之和（脚本会校验，不一致直接报错）
- `single.answer` 为正确项索引（0 起）；`multiple.answers` 为索引数组
- `fill.answers` 列出所有可接受写法（判分时自动去空格与标点、任一匹配即得分）
- `short` 必须给 `reference`（参考答案）和 `key_points`（评分要点，标注分值，合计=该题分值）
- `short` 可选 **`keywords` 关键词自动批改**：数组内每项为 `{"word": "…", "score": 1}` 或 `{"words": ["…", "…"], "score": 1}`（同义词，任一命中即得该项分）；多条命中可累加、总分封顶为本题目题分值，且**各项 score 合计必须=该题分值**（脚本校验）。**命中词务必取自参考答案的实质结论/术语**（病名、证型、治法要点、方名等），写错或漏写答案词才不得分；不能把题干要求词（如“辨病”“代表方”字样）当命中词——那只是答题要求，写了不等于答对。配置了 keywords 后，提交即按命中自动给分（替代人工自评），未配置时维持人工自评。**卷面作答前不会显示命中词（防泄题），只提示按要点自动批改与满分**
- **题干（stem）只放病案资料与作答要求**：病案出处（如“节选自某医案”）、答题依据/辨治提示（如“按《中医内科学》肺胀辨治”）等会暴露线索的内容一律放 `reference`/`explanation`，作答前对考生不可见
- 每题都要有 `source`（知识库出处）和 `explanation`

### 第 4 步：生成交付物

```bash
cd {skill目录}/scripts
python build_exam_html.py --exam exam.json --output-dir 试卷输出 --name "{试卷名}"

# 答案卷转 PDF（可选步骤，仅当用户明确要求 PDF/打印版时执行）
# 首选 Chrome：
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless --disable-gpu \
  --print-to-pdf="试卷输出/{试卷名}_答案卷.pdf" --no-pdf-header-footer \
  "试卷输出/{试卷名}_答案卷.html"
# ⚠️ 若 Chrome 无头静默失败（部分机器出现），改用 Edge（已验证可行）：
"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless --disable-gpu \
  --no-sandbox --user-data-dir="$TEMP/edge_pdf_profile" \
  --print-to-pdf="{绝对路径}/{试卷名}_答案卷.pdf" --no-pdf-header-footer \
  "file:///{答案卷HTML的绝对路径}"
# Edge 转换要点：--print-to-pdf 与输入 URL 均用绝对路径/ file:/// URL，并加 --user-data-dir
```

产出 3 个文件：`{试卷名}.html`（交互试卷）、`{试卷名}_答案卷.html`、`{试卷名}_答案卷.pdf`。

**交互试卷功能（脚本已内置，无需手写）：**
- 顶部学生姓名输入，未填提交会被拦截
- 单选→单选框；多选→复选框；填空→输入框；简答/名词解释/论述→文本域
- 底部「提交试卷·查看成绩」按钮 → **原地立即批改**：
  - 客观题自动判分，逐题显示 ✓/△/✗ 与得分；正确选项绿色高亮、错选红色
  - 主观题：若配置了 `keywords` → **按关键词自动判分**（命中逐条标绿 ✓/标红 ✗ 并给分、展示参考答案）；未配置 → 展开参考答案+评分要点，学生按要点自评填分（未填按 0 分）
  - 成绩卡：姓名、客观题得分、主观题（关键词自动批改/自评）、已答题数、正确率、总分+进度条
- **成绩自动上报服务器**（PWA 学习中心场景）：
  - 提交批改的同时，向 `submit_url`（默认 `/api/exam/submit`，可用 `--submit-url` 修改）发起 **POST，Content-Type: application/json，body 为成绩 JSON**
  - 发送顺序：`navigator.sendBeacon`（页面关闭也能送达）→ 失败则 `fetch keepalive POST` → 均失败则 localStorage 留档（key 前缀 `exam_result:`）
  - 成绩数据同时挂载 `window.__LAST_EXAM_RESULT__`，宿主系统/自动化测试可直接读取
  - `exam_id` 未在 exam.json 提供时按卷名自动生成稳定 ID（`exam-<md5前10位>`），服务器靠它关联试卷
  - `exam_id` 同时写入试卷 HTML 三个位置：开头 HTML 注释、`<head>` meta 标签（`exam-id`/`exam-submit-url`/`exam-total-score`）、内嵌 `const EXAM = {...}` 数据——服务器端解析 meta 即可建立试卷清单

**服务器需拦截的字段 —— `POST /api/exam/submit`，body 顶层结构：**

```json
{
  "type": "exam_result",          // 固定值，服务器以此识别成绩上报
  "version": 1,
  "exam_id": "exam-dc6aefb456",   // 试卷 ID（同一卷所有学生相同）
  "exam_title": "中医综合·胸痹专题演示卷",
  "student_name": "张三",
  "submitted_at": "2026-09-05T10:30:00.000Z",
  "total_score": 22,              // 满分
  "final_score": 15,              // 总得分 = objective_score + subjective_self
  "objective_score": 10, "objective_max": 12,
  "subjective_self": 5,  "subjective_max": 10,
  "subjective_auto": 3,           // 主观题中按 keywords 自动批改的得分（0-可选项，无则略/为 0）
  "answered_count": 6, "question_count": 7,
  "correct_count": 3,  "objective_count": 6,
  "accuracy": 50,                 // 客观题正确率（百分数）
  "answers": [                    // 逐题明细
    {"qid": 1, "type": "single", "max_score": 2, "score": 2, "answer": 1, "correct": true},
    {"qid": 3, "type": "multiple", "max_score": 3, "score": 0, "answer": [0], "correct": false},
    {"qid": 5, "type": "fill", "max_score": 2, "score": 0, "answer": "错误答案", "correct": false},
    {"qid": 7, "type": "short", "max_score": 8, "score": 8, "answer": "…文字…", "correct": null, "self_score": 8}
  ]
}
```

服务器端最小实现示例（Node/Express）：

```js
app.post("/api/exam/submit", express.json({ limit: "256kb" }), (req, res) => {
  const r = req.body;
  if (r.type !== "exam_result") return res.status(400).json({ error: "bad type" });
  db.saveExamResult(r);            // 按 exam_id + student_name + submitted_at 落库
  res.json({ ok: true });
});
```

要点：接口返回 2xx 即视为上报成功；上报失败不影响学生查看成绩（本地留档兜底）；服务器可选读取 `localStorage` 中 `exam_result:*` 键做离线补录。
  - 提交后所有作答区锁定，防止改答案

### 附：命题模板（题型规范）

**A1 型（单句最佳选择题）——考记忆理解**
```
{题干：概念/功效/组成/定位的一句话提问}
A. {干扰项}  B. {干扰项}  C. {正确项}  D. {干扰项}  E. {干扰项}
```
规则：5 个选项；干扰项须同范畴（都是方名/都是穴名）；避免「以上都对」。

**A2 型（病例摘要最佳选择题）——考辨证应用**
```
患者{性别年龄}，{主诉}，{现病史摘要}。查：{舌脉关键}。
其证型是 / 最宜选用的方剂是 / 最适宜的治法是：
A-E 选项
```
规则：题干含四诊要点（尤其舌脉，是辨证钥匙）；干扰证型须与主证有真实鉴别点。

**B1 型（配伍题）——考鉴别对比**
```
（1-3题共用备选答案）
A. 银翘散  B. 桑菊饮  C. 荆防败毒散  D. 参苏饮  E. 加减葳蕤汤
1. 风热犯表之感冒，宜选（ ）
2. 风寒束表之感冒，宜选（ ）
3. 气虚感冒，宜选（ ）
```

**填空 / 名词解释 / 简答（考研向）**
- 填空：经典条文挖空（如「阳浮而阴弱，阳浮者，____；阴弱者，____」）
- 名词解释：证型/术语（含定义+病机+代表方）
- 简答：病机演变 / 方剂鉴别 / 治法分类

### 附：答案与解析要求（每题必附，写入 exam.json 的 explanation/source 字段）

```
【解析】本题考查{考点}。{正确项的理由，含病机逻辑}。
{各干扰项逐一说明错在哪，这是提分关键。}
【出处】《中医内科学》· 肺系病证· 咳嗽章节 / 《伤寒论》第X条
```

### 第 4 步：质量自检（交付前逐项核对）

- [ ] 每题只有一个正确答案（多选除外），无歧义
- [ ] 干扰项有真实鉴别意义，不凑数
- [ ] A2 题舌脉信息足以支持辨证结论
- [ ] 答案与知识库原文核对一致
- [ ] 难度分布合理（简单:中等:困难 ≈ 3:5:2）
- [ ] 无重复考点（同份试卷内）
- [ ] 各题分值合计 = 用户确认的总分
- [ ] 简答题 key_points 分值合计 = 该题分值
- [ ] 配置 keywords 的简答题：各项 score 合计 = 该题分值，且命中词与题干要求一致（如“辨病/辨证/核心病机/治法/代表方”）
- [ ] 交互试卷已在本地打开验证：提交、批改、成绩卡均正常

---

## 二、专项场景规则

### 执业医师风格
- 严格按 A1/A2/B1 题型；题干简洁（A2 病例一般 ≤100 字）；解析含「考点提炼」
- 覆盖大纲高频：辨证选方 > 治法 > 病因病机 > 腧穴主治 > 中药功效

### 考研风格
- 名词解释、简答、论述为主；考经典条文默写与方证鉴别
- 论述题给答题框架（如「试述胸痹的病机与分型论治」→ 总病机 + 分证论治表 + 代表方条文）

### 经典原文题（本知识库特色）
- 条文填空、条文类方归属、「某方主之」的证候还原
- 条文必须用检索脚本核对，标注出处（书名+篇名+条文序号）

### 针灸题
- 腧穴定位（用 3Dbody 描述定位规则，借鉴 zhongyi-xuexi skill）
- 主治配穴、五输穴/八会穴/八脉交会穴归属、针灸处方（主穴+配穴+操作）

### 磨耳跟读自测（配合用户的 MP3 跟读系列）
- 口语化播报题目：「第一题……答案……解析……」
- 每题 30 秒内讲完，适合音频形式

---

## 三、组卷规则

一份完整试卷结构（默认 10 题版）：

| 题号 | 题型 | 数量 | exam.json type | 说明 |
|------|------|------|---------------|------|
| 1-4 | A1 | 4 | single | 基础概念 |
| 5-8 | A2 | 3 | single | 病例辨证 |
| 9-10 | B1 | 2 组 | multiple（或拆为 single） | 鉴别对比 |

**默认交付：仅交互式 HTML 试卷 + 答案卷 HTML**（见「标准交付物」）；PDF 仅在用户要求时转换。用户仅要 Markdown 版时才输出纯文本卷（答案解析置末）。

## 四、内容红线

- 不得出诊断不明、答案存争议的题（学界有争议的知识点注明「存在学术争议」）
- 涉及毒性药物剂量的题目，解析中必须附安全剂量说明
- 现代医学对照病名仅作参考背景，不作为答案依据
