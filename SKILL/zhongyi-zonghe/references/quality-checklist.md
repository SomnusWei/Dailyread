# 中医讲义质量检查清单

> 分级检查：P0（致命）→ P1（重要）→ P2（一般）

---

## P0 级（致命错误，必须修复）

### 内容准确性
- [ ] 每个证型的"症状→病机→治法→方剂"逻辑链条自洽
- [ ] 所有方剂组成完整，君、臣、佐、使标注正确
- [ ] 证型分类与教材一致，无遗漏或错配
- [ ] 治则治法与证型病机对应正确
- [ ] 含毒性药物（附子、川乌、草乌、朱砂、雄黄、细辛、马钱子等）必须标注使用注意和禁忌
- [ ] 无重大医学常识错误（如虚实错辨、寒热颠倒）
- [ ] 疾病概念定义准确，与教材一致

### 格式正确性
- [ ] HTML 标签正确闭合（`</body></html>` 完整）
- [ ] 无未闭合的 `<div>`、`<table>`、`<ul>` 等标签
- [ ] 文件编码为 UTF-8，无乱码

---

## P1 级（重要问题，应该修复）

### 结构完整性
- [ ] 讲义结构完整：封面 + 目录 + 总论 + 各论 + 附录
- [ ] 目录锚点 `href` 与正文 `id` 一一对应，无失效链接
- [ ] 总论包含：脏腑生理、病因病机总览、辨证治疗原则
- [ ] 各论每病包含：理（概念+病因病机+诊断鉴别）、法（治则）、方药（证型+方剂+方解+药物）
- [ ] 附录包含：方剂速查表、药物速查表
- [ ] 每章末尾有小结

### 知识准确性
- [ ] 每味药物的性味归经准确
- [ ] 药物功效主治描述准确
- [ ] 病因病机分析符合中医理论
- [ ] 诊断与鉴别诊断要点清晰准确
- [ ] 交叉引用正确（"详见XX病XX证"指向正确位置）

### 排版规范性
- [ ] 章节分页正确（每章从新页开始）
- [ ] 表格内容完整，无错位、无断行
- [ ] 证型卡片（.zheng-bg）无跨页断裂
- [ ] 药物详解块（.yao-bg）无跨页断裂
- [ ] 无大块空白区域

### 交叉引用
- [ ] 方剂速查表包含所有正文中出现的方剂
- [ ] 药物速查表包含所有展开详解的药物
- [ ] 同一方剂在不同疾病中首次出现完整讲解，后续有引用说明
- [ ] 跨系统疾病有明确的引用说明

---

## P2 级（一般问题，酌情修复）

### 排版细节
- [ ] 标点符号规范统一（全角标点）
- [ ] 字号、间距、缩进一致
- [ ] 颜色使用符合主题色系
- [ ] 无多余空行和空格
- [ ] 术语表述统一（如"咳喘"vs"喘咳"、"证候"vs"证型"）
- [ ] 目录层级缩进正确
- [ ] 表格对齐整齐
- [ ] 序号格式统一

### 文字细节
- [ ] 无明显OCR错误和错别字
- [ ] 药名、方名无错字（如黄芩≠黄苓、白术≠白木、炙甘草≠灸甘草）
- [ ] 引用原文无遗漏
- [ ] 数字和单位格式统一

---

## 快速验证命令（PowerShell）

```powershell
# ========== 格式检查 ==========

# 1. 检查HTML标签闭合
$htmlPath = "讲义.html"

# 检查结束标签
$bodyClose = Select-String -Path $htmlPath -Pattern "</body>"
$htmlClose = Select-String -Path $htmlPath -Pattern "</html>"
Write-Output "body闭合: $($bodyClose.Count), html闭合: $($htmlClose.Count)"

# 检查div配对
$openDiv = (Select-String -Path $htmlPath -Pattern '<div ').Count
$closeDiv = (Select-String -Path $htmlPath -Pattern '</div>').Count
Write-Output "div开始: $openDiv, div结束: $closeDiv (差值应接近0)"

# 2. 检查锚点匹配
$hrefs = (Select-String -Path $htmlPath -Pattern 'href="#[a-z]').Count
$ids = (Select-String -Path $htmlPath -Pattern 'id="chap-|id="sec-|id="app-').Count
Write-Output "目录链接: $hrefs, 章节锚点: $ids"

# 3. 检查文件末尾
Write-Output "=== 文件末尾5行 ==="
Get-Content $htmlPath -Tail 5

# 4. 检查常见OCR错字
$typos = @("黄苓", "白木", "灸甘草", "羌话", "蒿本", "伏苓", "半厦", "构杞", "黄茋")
foreach ($typo in $typos) {
    $matches = Select-String -Path $htmlPath -Pattern $typo
    if ($matches) {
        Write-Output "⚠️  可能有错字 '$typo': $($matches.Count)处"
    }
}

# 5. 检查毒性药物是否标注使用注意
$toxicHerbs = @("附子", "川乌", "草乌", "朱砂", "雄黄", "细辛", "马钱子")
foreach ($herb in $toxicHerbs) {
    $count = (Select-String -Path $htmlPath -Pattern $herb).Count
    if ($count -gt 0) {
        Write-Output "ℹ️  含毒性药物 '$herb' 共 $count 处，请确认是否标注了使用注意"
    }
}

# 6. 检查文件大小
$file = Get-Item $htmlPath
Write-Output "`n文件大小: $([math]::Round($file.Length/1KB, 1)) KB"
```

---

## 人工检查要点

### 快速通读（10分钟）
1. 翻一遍目录，确认章节完整
2. 随机打开3-5个章节，检查结构是否完整
3. 查看附录速查表，确认无明显遗漏
4. 检查PDF分页是否正常

### 重点抽查（20分钟）
1. 选1个疾病，通读全章，检查"理-法-方-药"逻辑是否通顺
2. 选2首方剂，核对组成和方解是否正确
3. 选3味中药，核对性味归经和功效
4. 检查所有含毒性药物的段落，确认有使用注意

---

## 常见错误速查

| 错误类型 | 示例 | 检查方法 |
|----------|------|----------|
| OCR错字 | 黄芩→黄苓、白术→白木、炙→灸 | 搜索常见错字列表 |
| 方剂组成遗漏 | 少了佐药或使药 | 对照方剂学教材核对 |
| 性味归经错误 | 性寒写成性温 | 对照中药学教材核对 |
| 证型张冠李戴 | 把A病的证型写到B病 | 对照中医内科学核对 |
| 治法与证型不对应 | 阴虚证用温阳法 | 通读每证"症状→治法→方剂"逻辑链 |
| 锚点失效 | href与id不匹配 | 统计数量+抽查几个 |
| 标签未闭合 | 缺少 </div> 或 </table> | PowerShell统计开闭标签数 |
