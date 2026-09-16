#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成 12 章知识地图（仓颉 Step 2 · 04-knowledge-map.md）。

输出内容：
  1. 章节总表：集号区段 / 时长 / 字数 / 核心考点数
  2. 每章明细：分集清单 + 四类高价值信号行（考点边界、记忆框架、口诀套路、临床联系）
  3. 全篇框架类表述汇总（用于 L1 教学主张与 L6 讲解套路提取）

用法：
    python build_knowledge_map.py            # 全量
    python build_knowledge_map.py --min-chars 3000
"""
import argparse
import json
import os
import re
import time

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
FIXED = os.path.join(INBOX, "transcripts_fixed")
OUT = os.path.join(INBOX, "distill", "references", "research", "04-knowledge-map.md")
EPS = os.path.join(INBOX, "episodes.json")
MAN = os.path.join(INBOX, "manifest.json")

# 生理学 12 章 → (标题关键词, 集号区段)
CHAPTERS = [
    ("绪论", ["绪论", "绪言"], (1, 1)),
    ("细胞的基本功能", ["细胞", "电", "肌"], (2, 12)),
    ("血液", ["血液", "血"], (13, 19)),
    ("血液循环", ["循环", "心", "血管", "血压"], (20, 33)),
    ("呼吸", ["呼吸", "肺"], (34, 40)),
    ("消化与吸收", ["消化", "吸收", "胃肠"], (41, 46)),
    ("能量代谢与体温", ["代谢", "体温", "能量"], (47, 50)),
    ("尿的生成和排出", ["尿", "肾"], (51, 56)),
    ("感觉器官的功能", ["感觉", "感官", "眼", "耳"], (57, 59)),
    ("神经系统的功能", ["神经", "突触", "反射"], (60, 66)),
    ("内分泌", ["内分泌", "激素", "垂体", "肾上", "甲状腺", "胰岛"], (67, 71)),
    ("生殖", ["生殖", "月经", "妊娠"], (72, 73)),
]

# 四类高价值信号（正则 → 类别）
SIGNALS = [
    ("考点边界", re.compile(r"考研|考纲|必考|考点|不考|考试|重点|记住|一定要|背下来|必须掌握")),
    ("记忆框架", re.compile(r"口诀|框架|思路|主线|分三|分四|三个层面|四个方面|总结一下|归纳|一句话")),
    ("机制推演", re.compile(r"为什么|机制|原理|推导|逻辑|本质|关键在于|实际上")),
    ("临床联系", re.compile(r"临床上|病人|患者|疾病|症状|病例|医院|诊断|治疗")),
]
TS = re.compile(r"^\[(\d{2}):(\d{2}):(\d{2})\]\s*(.*)$")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-chars", type=int, default=3000)
    ap.add_argument("--max-signal-per-chapter", type=int, default=14)
    a = ap.parse_args()

    eps = {e["index"]: e for e in json.load(open(EPS, encoding="utf-8"))}
    man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}
    files = sorted(f for f in os.listdir(FIXED)
                   if f.endswith(".fixed.txt") and not f.startswith("_"))

    # 读入全部转写稿：{集号: [(ts, text), ...]}
    ep_lines = {}
    for f in files:
        m = re.match(r"P(\d{2})_", f)
        if not m:
            continue
        i = int(m.group(1))
        rows = []
        for line in open(os.path.join(FIXED, f), encoding="utf-8"):
            mm = TS.match(line.strip())
            if mm:
                rows.append((f"{mm.group(1)}:{mm.group(2)}:{mm.group(3)}", mm.group(4)))
        ep_lines[i] = rows

    L = []
    L.append("# 04 · 知识地图（生理学 12 章 × 刘忠保讲授框架）\n")
    L.append(f"> 生成时间：{time.strftime('%Y-%m-%d %H:%M')}　|　"
             f"已覆盖 {len(ep_lines)} 集 / 共 73 集\n")
    L.append("> 说明：本文件是仓颉蒸馏的**知识导航层**——只做定位与信号汇聚，"
             "结论性内容一律以转写稿原文＋时间戳为准。\n")

    # 一、章节总表
    L.append("\n## 一、章节总表\n")
    L.append("| 章 | 集号区段 | 已转写集数 | 时长 | 字数 | 考点边界信号 | 记忆框架信号 |")
    L.append("|----|----------|-----------|------|------|--------------|--------------|")
    chapter_payload = []
    for name, kws, (lo, hi) in CHAPTERS:
        idxs = sorted(i for i in ep_lines if lo <= i <= hi)
        dur = sum(eps[i]["duration"] for i in idxs if i in eps)
        chars = sum(man.get(str(i), {}).get("chars", 0) for i in idxs)
        sig_count = {}
        for cat, _ in SIGNALS:
            sig_count[cat] = 0
        for i in idxs:
            for ts, txt in ep_lines[i]:
                for cat, pat in SIGNALS:
                    if pat.search(txt):
                        sig_count[cat] += 1
                        break
        L.append(f"| **{name}** | P{lo:02d}–P{hi:02d} | {len(idxs)} | {dur/3600:.1f} h | "
                 f"{chars:,} | {sig_count['考点边界']} | {sig_count['记忆框架']} |")
        chapter_payload.append((name, kws, idxs))

    # 二、章节明细
    L.append("\n## 二、章节明细与高价值信号\n")
    for name, kws, idxs in chapter_payload:
        L.append(f"\n### {name}\n")
        L.append("**分集**：" + ("、".join(f"P{i:02d} {eps[i]['title']}" for i in idxs)
                                if idxs else "（尚未转写）") + "\n")
        if not idxs:
            continue
        for cat, pat in SIGNALS:
            picked = []
            for i in idxs:
                for ts, txt in ep_lines[i]:
                    if pat.search(txt) and len(txt) >= 6:
                        picked.append(f"- `P{i:02d} [{ts}]` {txt}")
            if picked:
                L.append(f"\n**{cat}**（共 {len(picked)} 条，列前 {a.max_signal_per_chapter} 条）\n")
                L.extend(picked[:a.max_signal_per_chapter])
                L.append("")

    # 三、全篇框架类表述（L1/L6 候选）
    L.append("\n## 三、全篇「框架/主张」类表述汇总（L1 · L6 候选池）\n")
    top_pat = re.compile(r"我一直|我的观点|我认为|我给同学们|提一个思路|一句话|本质|学这门课|"
                         r"不要死记|不要背|理解|串起来|主线|整体|从.*?开始.*?结束")
    pool = []
    for i in sorted(ep_lines):
        for ts, txt in ep_lines[i]:
            if top_pat.search(txt) and 8 <= len(txt) <= 120:
                pool.append((i, ts, txt))
    L.append(f"（共 {len(pool)} 条候选）\n")
    for i, ts, txt in pool[:120]:
        L.append(f"- `P{i:02d} [{ts}]` {txt}")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("已生成:", OUT)
    print(f"覆盖 {len(ep_lines)} 集 | 章节 {len(chapter_payload)} | 框架候选 {len(pool)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
