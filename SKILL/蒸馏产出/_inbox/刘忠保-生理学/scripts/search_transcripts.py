#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""转写稿全文检索（带时间戳），供仓颉提取阶段取证。

用法：
    python search_transcripts.py "我一直"                       # 全库检索
    python search_transcripts.py "口诀,记住,不要背" --chapter 细胞   # 多关键词 + 章过滤
    python search_transcripts.py "为什么" --ep 2-12 --max 30       # 集号范围 + 上限
    python search_transcripts.py "本质" --context 1                # 带前后各 1 句上下文
    python search_transcripts.py "受体" --ep 3 --out hits.md       # 结果写入文件
"""
import argparse
import json
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
FIXED = os.path.join(INBOX, "transcripts_fixed")
EPS = os.path.join(INBOX, "episodes.json")

TS = re.compile(r"^\[(\d{2}:\d{2}:\d{2})\]\s*(.*)$")

CHAPTER_RANGES = {
    "绪论": (1, 1), "细胞": (2, 12), "血液": (13, 19), "循环": (20, 33),
    "呼吸": (34, 40), "消化": (41, 46), "代谢": (47, 50), "泌尿": (51, 56),
    "感觉": (57, 59), "神经": (60, 66), "内分泌": (67, 71), "生殖": (72, 73),
}


def load_eps():
    return {e["index"]: e for e in json.load(open(EPS, encoding="utf-8"))}


def parse_ep(spec):
    if not spec:
        return None
    if "-" in spec:
        a, b = spec.split("-")
        return set(range(int(a), int(b) + 1))
    return {int(spec)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", help="关键词，逗号分隔（任一命中即算）")
    ap.add_argument("--chapter", default="", help="章名过滤：" + "/".join(CHAPTER_RANGES))
    ap.add_argument("--ep", default="", help="集号或范围，如 3 或 2-12")
    ap.add_argument("--context", type=int, default=0, help="附带前后句数")
    ap.add_argument("--max", type=int, default=60, help="最多输出条数")
    ap.add_argument("--per-file", type=int, default=8, help="每集最多输出条数")
    ap.add_argument("--out", default="", help="结果写入文件（markdown）")
    a = ap.parse_args()

    kws = [k.strip() for k in a.keywords.split(",") if k.strip()]
    eps = load_eps()
    ep_filter = parse_ep(a.ep)
    if a.chapter and a.chapter in CHAPTER_RANGES:
        lo, hi = CHAPTER_RANGES[a.chapter]
        rng = set(range(lo, hi + 1))
        ep_filter = rng if ep_filter is None else (ep_filter & rng)

    out = []
    total = 0
    for f in sorted(os.listdir(FIXED)):
        m = re.match(r"P(\d{2})_(.+)\.fixed\.txt$", f)
        if not m or f.startswith("_"):
            continue
        i = int(m.group(1))
        if ep_filter and i not in ep_filter:
            continue
        rows = []
        for line in open(os.path.join(FIXED, f), encoding="utf-8"):
            mm = TS.match(line.strip())
            if mm:
                rows.append((mm.group(1), mm.group(2)))
        got = 0
        for n, (ts, txt) in enumerate(rows):
            if not any(k in txt for k in kws):
                continue
            ctx = ""
            if a.context:
                lo = max(0, n - a.context)
                hi = min(len(rows), n + a.context + 1)
                ctx = " ".join(t for _, t in rows[lo:hi])
            title = eps.get(i, {}).get("title", "")
            out.append((i, title, ts, txt, ctx))
            got += 1
            total += 1
            if got >= a.per_file or total >= a.max:
                break
        if total >= a.max:
            break

    header = (f"# 转写稿检索结果\n\n- 关键词：{'、'.join(kws)}\n"
              f"- 范围：{a.chapter or '全库'}{(' / P' + a.ep) if a.ep else ''}\n"
              f"- 命中：{total} 条\n")
    lines = [header]
    for i, title, ts, txt, ctx in out:
        lines.append(f"- `P{i:02d} {title} [{ts}]` {txt}")
        if ctx:
            lines.append(f"      ↳ 上下文：{ctx}")
    text = "\n".join(lines) + "\n"
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"已写入 {a.out}（{total} 条）")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
