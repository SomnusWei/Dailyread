#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ASR 转写稿医学术语纠错（教材术语表 + 教材语料 + 模糊拼音三重校验）。

纠错规则：
  对转写稿中的中文 n-gram（n=3..9）：
    ① 该 n-gram **未在教材全文中出现**        → 强烈提示为 ASR 误识
    ② 该 n-gram 本身不是教材术语
    ③ 其无声调拼音与某教材术语的拼音 **相同（high）或编辑距离=1（medium）**
    ④ 与目标术语字数相同
  → 判定为误识并替换

用法：
    python correct_terms.py <原始转写txt> <纠错后txt> [报告tsv]
"""
import os
import re
import sys
from collections import Counter, defaultdict

from pypinyin import lazy_pinyin

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTBOOK = r"c:\Users\somnu\.trae-cn\skills\yixue-zonghe\西医教材\生理学 （第10版）.txt"
TERMS = os.path.join(BASE, "terms", "terms.txt")

CN_RUN = re.compile(r"[\u4e00-\u9fff]{3,}")
TS = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s*")

# 虚词/口语字黑名单：医学标准术语几乎不含这些字，含之则判定为「正常句子片段」而非误识
# （刻意不含 中/下/上/内/外/前/后/去/带/听/觉/道 等仍见于术语的字）
FUNC_CHARS = set(
    "的了是不在和与等这那我你他她们就都还也而且很没把被吗吧呢啊一"
    "个们么什怎为以于之其所以如果但因故虽则并且或更"
    "搞弄说讲想让给找拿走该别挺太真唱玩写念买卖"
)


def pykey(s: str) -> str:
    return "".join(lazy_pinyin(s))


def dist1(a: str, b: str) -> bool:
    """编辑距离是否 ≤1（等长时只算替换）。"""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        return sum(1 for x, y in zip(a, b) if x != y) <= 1
    # 长度差 1：插入/删除
    if len(a) > len(b):
        a, b = b, a
    i = j = 0
    diff = 0
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            i += 1
            j += 1
        else:
            diff += 1
            j += 1
            if diff > 1:
                return False
    return True


def load_terms():
    terms = [t.strip() for t in open(TERMS, encoding="utf-8").read().splitlines() if t.strip()]
    term_set = set(terms)
    exact = {}
    buckets = defaultdict(list)
    for t in terms:
        p = pykey(t)
        exact.setdefault(p, t)
        buckets[(len(t), len(p))].append((p, t))
    return term_set, exact, buckets


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    raw_path, out_path = sys.argv[1], sys.argv[2]
    report_path = sys.argv[3] if len(sys.argv) > 3 else out_path.replace(".txt", "_corrections.tsv")

    term_set, exact, buckets = load_terms()
    print(f"[load] 术语 {len(term_set)} 条", flush=True)
    book = re.sub(r"\s+", "", open(TEXTBOOK, encoding="utf-8", errors="ignore").read())
    print(f"[load] 教材语料 {len(book)} 字", flush=True)

    _bcache = {}

    def book_count(s: str) -> int:
        c = _bcache.get(s)
        if c is None:
            c = book.count(s)
            _bcache[s] = c
        return c

    lines = open(raw_path, encoding="utf-8").read().splitlines()
    raw_text = "\n".join(lines)
    out_lines, records, pending = [], [], []
    total_chars = 0

    for ln, line in enumerate(lines, 1):
        m = TS.match(line)
        prefix = line[:m.end()] if m else ""
        body = line[m.end():] if m else line
        if not body.strip() or body.startswith("#"):
            out_lines.append(line)
            continue
        total_chars += len(body)
        chars = list(body)
        hits = []
        for run in CN_RUN.finditer(body):
            seg, start = run.group(0), run.start()
            n = len(seg)
            for size in range(min(9, n), 2, -1):
                for i in range(0, n - size + 1):
                    ng = seg[i:i + size]
                    if ng in term_set:
                        continue
                    # 含虚词/口语字 → 判为正常句子片段，不做纠正（防误纠）
                    if any(ch in FUNC_CHARS for ch in ng):
                        continue
                    p = pykey(ng)
                    tgt, conf = None, None
                    if p in exact and exact[p] != ng and len(exact[p]) == size:
                        tgt, conf = exact[p], "high"
                    else:
                        for bp, bt in buckets.get((size, len(p)), ()):  # noqa: B905
                            if bt != ng and dist1(p, bp):
                                tgt, conf = bt, "medium"
                                break
                    if not tgt:
                        continue
                    # 二字词风险高：仅接受「精确拼音 + 目标词在本集已出现」的严格条件
                    if size == 2 and not (conf == "high" and tgt in raw_text):
                        continue
                    # 教材中出现过 → 视为正常词，不改。因源片段最短 3 字，子串巧合概率极低，
                    # 故阈值取 1 即可（可拦住「单向转运」这类真实术语被误改为「反向转运」）
                    s_abs, e_abs = start + i, start + i + size
                    if book_count(ng) >= 1:
                        continue
                    # 上下文护栏：向左/右各扩一字后若形成教材中常见的长词，说明命中的只是长词的一部分
                    ext_ok = True
                    for lo, hi in ((s_abs - 1, e_abs), (s_abs, e_abs + 1)):
                        if lo < 0 or hi > len(body):
                            continue
                        ext = body[lo:hi]
                        if len(ext) == size + 1 and book_count(ext) >= 2:
                            ext_ok = False
                            break
                    if not ext_ok:
                        continue
                    # medium 置信度需过「自洽性」二次校验：该术语须在本集原始稿中已正确出现过，
                    # 否则只登记待复核、不直接改写（防误纠）
                    if conf == "medium" and tgt not in raw_text:
                        pending.append((ln, ng, tgt, body))
                        continue
                    hits.append((start + i, start + i + size, ng, tgt, conf))
        hits.sort(key=lambda x: (x[0], -(x[1] - x[0])))
        used = []
        for s, e, ng, tgt, conf in hits:
            if any(not (e <= us or s >= ue) for us, ue in used):
                continue
            used.append((s, e))
            records.append((ln, ng, tgt, conf, body))
            for k in range(s, e):
                chars[k] = tgt[k - s] if k - s < len(tgt) else ""
        out_lines.append(prefix + "".join(chars))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out_lines))
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("行号\t误识\t纠正为\t置信度\t原句\n")
        for r in records:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\n")
    pend_path = report_path.replace("_corrections.tsv", "_pending_review.tsv")
    with open(pend_path, "w", encoding="utf-8") as f:
        f.write("行号\t疑似误识\t建议术语\t原句\n")
        for r in pending:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n")

    cnt = Counter(r[2] for r in records)
    conf = Counter(r[3] for r in records)
    print("=" * 62)
    print(f"已应用纠错 {len(records)} 处（high {conf['high']} / medium {conf['medium']}）"
          f" | 涉及术语 {len(cnt)} 个 | 正文 {total_chars} 字")
    print(f"待复核（未改写）{len(pending)} 处 → {os.path.basename(pend_path)}")
    if total_chars:
        print(f"纠错密度：每千字 {len(records) / total_chars * 1000:.2f} 处")
    print("高频纠正 Top20:")
    for t, c in cnt.most_common(20):
        print(f"  {c:>4} × {t}")
    print("报告:", report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
