#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中医知识库全库检索脚本（跨 700+ 古籍 + 现代教材）
用法示例：
  python search_textbooks.py --keyword 桂枝汤                      # 全库搜
  python search_textbooks.py --keyword 胸痹 --category 伤寒论,金匮要略   # 按类目过滤
  python search_textbooks.py --keyword 足三里 --files "经络腧穴学.txt,299-针灸大成.txt"  # 指定文件
  python search_textbooks.py --keyword 半夏 --context 8 --max-hits 50   # 调上下文与命中数
输出：命中文件统计 + 每处命中的上下文摘录（自动跳过超小文件与二进制）。
"""

import os
import re
import argparse
import json
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from text_utils import read_text_lines, clean_ancient_markup  # noqa: E402

# 默认教材目录 = 与本 skill 同级的「教材」资料夹（安装时把教材放到 skill 根目录下，
# 即与 SKILL.md 同一文件夹；不同位置可用 --textbook-dir 覆盖）
def _default_textbook_dir(track="中医"):
    sub = "中医教材" if track == "中医" else "西医教材"
    return os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", sub))

TRACK_CHOICES = ["中医", "西医"]

# ---------- 跨库检索：专家特化库 / 蒸馏产出 ----------
# 相对 skill 根目录的固定专家库路径
_SKILL_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

SOURCE_CHOICES = ["all", "textbook", "nihaixia", "shixuemin", "distilled"]

# 专家库/蒸馏库中参与检索的文件扩展名（SKILL.md 与 references 均为文本素材）
EXPERT_EXTS = (".md", ".txt")

# 单文件扫描上限，避免超大文件（如 134KB 的 SKILL.md 尚可，数百 MB 的极端文件跳过）
_MAX_FILE_BYTES = 20 * 1024 * 1024


def _iter_expert_files(source):
    """收集专家特化库 / 蒸馏产出 下参与检索的文本文件。

    返回 [(显示名, 绝对路径, 来源标签), ...]
    """
    entries = []
    if source in ("all", "nihaixia"):
        root = os.path.join(_SKILL_ROOT, "倪海厦体系")
        for name, path in _walk(root):
            entries.append((f"倪师/{name}", path, "nihaixia"))
    if source in ("all", "shixuemin"):
        root = os.path.join(_SKILL_ROOT, "石学敏体系")
        for name, path in _walk(root):
            entries.append((f"石师/{name}", path, "shixuemin"))
    if source in ("all", "distilled"):
        root = os.path.join(_SKILL_ROOT, "蒸馏产出")
        for name, path in _walk(root):
            entries.append((f"蒸馏/{name}", path, "distilled"))
    return entries


def _walk(root):
    """递归遍历 root 下的文本文件，返回 [(相对路径, 绝对路径), ...]，按路径排序。"""
    if not os.path.isdir(root):
        return []
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for fn in filenames:
            if not fn.lower().endswith(EXPERT_EXTS):
                continue
            full = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(full) > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            rel = os.path.relpath(full, root).replace("\\", "/")
            out.append((rel, full))
    out.sort(key=lambda x: x[0])
    return out


# 类目 -> 文件名关键词（与 build_textbook_index.py 保持一致，简化版）
CATEGORY_HINTS = {
    "现代教材": ["中医基础理论", "中医诊断学", "中药学", "方剂学", "中医内科学", "经络腧穴学",
                "针灸治疗学", "石学敏", "中医大辞典", "黄帝内经》"],
    "伤寒论": ["伤寒"],
    "金匮要略": ["金匮"],
    "本草": ["本草", "药性", "药征", "炮炙", "食疗", "食治", "别录", "得配"],
    "针灸推拿": ["针灸", "针经", "灸", "经络", "经穴", "腧穴", "推拿", "按摩", "子午流注", "十四经"],
    "医经": ["内经", "素问", "灵枢", "难经", "类经", "太素", "外经"],
    "温病瘟疫": ["温病", "温热", "温疫", "瘟疫", "湿热", "霍乱", "时病"],
    "医案医话": ["医案", "医话", "临证", "经验", "验案", "寓意草", "医说"],
    "方书": ["方", "汤头", "局方", "剂"],
    "脉学诊法": ["脉", "望诊", "舌", "察病", "诊家"],
}


def match_category(filename, categories):
    """判断文件是否属于给定类目列表"""
    stem = os.path.splitext(filename)[0]
    name = re.sub(r"^\d+[\.\-]", "", stem)
    for cat in categories:
        if cat in CATEGORY_HINTS:
            for kw in CATEGORY_HINTS[cat]:
                if kw in name:
                    return True
    return False


def search_file(path, keywords, ctx_before, ctx_after):
    """在单个文件中搜索关键词，返回命中列表 [(kw, line_no, snippet)]

    自动处理编码：10 部现代教材为 UTF-8，701 部古籍为 GB18030。
    """
    hits = []
    lines = read_text_lines(path)

    matched_lines = set()
    for i, line in enumerate(lines):
        hit_kw = None
        for kw in keywords:
            if kw in line:
                hit_kw = kw
                break
        if hit_kw is None:
            continue
        # 去重：附近 8 行内已命中过则跳过
        if any(abs(i - m) < 8 for m in matched_lines):
            continue
        matched_lines.add(i)
        start = max(0, i - ctx_before)
        end = min(len(lines), i + ctx_after + 1)
        snippet = "".join(lines[start:end]).strip()
        snippet = clean_ancient_markup(snippet)
        hits.append((hit_kw, i + 1, snippet))
    return hits


def main():
    parser = argparse.ArgumentParser(description="中医知识库全库检索")
    parser.add_argument("--keyword", required=True, help="搜索关键词，多个用逗号分隔")
    parser.add_argument("--track", choices=["中医", "西医"], default="中医", help="医学体系：中医/西医（默认中医）")
    parser.add_argument("--textbook-dir", default=None, help="教材目录（不指定则按 --track 自动选择）")
    parser.add_argument("--category", default="", help="类目过滤，逗号分隔（如: 伤寒论,金匮要略）")
    parser.add_argument("--files", default="", help="指定文件名，逗号分隔（精确匹配）")
    parser.add_argument("--context", type=int, default=6, help="上下文行数（默认6）")
    parser.add_argument("--max-hits", type=int, default=20, help="每文件最多输出命中数（默认20）")
    parser.add_argument("--min-hits", type=int, default=1, help="文件至少命中次数才输出（默认1）")
    parser.add_argument("--quiet", action="store_true", help="只输出文件统计，不输出摘录")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出结果")
    parser.add_argument("--source", choices=SOURCE_CHOICES, default=None,
                        help="检索来源：all（中医默认，教材+倪师+石师+蒸馏产出）/ "
                             "textbook（仅教材）/ nihaixia（仅倪海厦体系）/ "
                             "shixuemin（仅石学敏体系）/ distilled（仅蒸馏产出）。"
                             "未指定时：中医=all，西医=textbook")
    args = parser.parse_args()

    # 默认来源：中医跨库，西医仅教材
    if args.source is None:
        args.source = "all" if args.track == "中医" else "textbook"

    if args.textbook_dir is None:
        args.textbook_dir = _default_textbook_dir(args.track)

    keywords = [k.strip() for k in args.keyword.split(",") if k.strip()]
    categories = [c.strip() for c in args.category.split(",") if c.strip()]
    specified_files = [f.strip() for f in args.files.split(",") if f.strip()]

    if not os.path.isdir(args.textbook_dir) and args.source != "distilled":
        print(f"❌ 教材目录不存在: {args.textbook_dir}")
        return

    # 教材库目标文件
    textbook_files = []
    if os.path.isdir(args.textbook_dir):
        textbook_files = sorted(
            f for f in os.listdir(args.textbook_dir)
            if f.lower().endswith(".txt")
        )

    # 组装检索目标：[(显示名, 绝对路径, 来源标签), ...]
    targets = []
    if args.source in ("all", "textbook"):
        if specified_files:
            picked = [f for f in textbook_files if f in specified_files]
            missing = set(specified_files) - set(picked)
            if missing:
                print(f"⚠️ 未找到文件: {', '.join(missing)}")
        elif categories:
            picked = [f for f in textbook_files if match_category(f, categories)]
        else:
            picked = textbook_files
        targets.extend(
            (f, os.path.join(args.textbook_dir, f), "textbook") for f in picked
        )

    if args.source in ("all", "nihaixia", "shixuemin", "distilled"):
        targets.extend(_iter_expert_files(args.source))

    src_label = {
        "all": "跨库（教材+倪师+石师+蒸馏产出）",
        "textbook": "仅教材",
        "nihaixia": "仅倪海厦体系",
        "shixuemin": "仅石学敏体系",
        "distilled": "仅蒸馏产出",
    }.get(args.source, args.source)

    print(f"🔍 关键词: {args.keyword}")
    print(f"📚 检索来源: {src_label}")
    print(f"📚 检索范围: {len(targets)} 个文件"
          + (f"（类目: {args.category}）" if categories and args.source in ("all", "textbook") else "")
          + (f"（指定文件）" if specified_files and args.source in ("all", "textbook") else ""))
    print()

    results = []
    file_stats = []
    for display_name, path, src_tag in targets:
        try:
            if os.path.getsize(path) < 500:  # 跳过近空文件
                continue
        except OSError:
            continue
        hits = search_file(path, keywords, args.context, args.context)
        if len(hits) >= max(args.min_hits, 1):
            file_stats.append((display_name, len(hits), src_tag))
            if not args.quiet:
                results.append({"file": display_name, "source": src_tag, "hits": [
                    {"keyword": kw, "line": ln, "snippet": sn}
                    for kw, ln, sn in hits[: args.max_hits]
                ]})

    file_stats.sort(key=lambda x: -x[1])
    print("=" * 62)
    print(f"命中文件统计（共 {len(file_stats)} 个文件命中）")
    print("=" * 62)
    for fname, count, src_tag in file_stats[:40]:
        print(f"  {fname}  [{count}处]")

    if args.json:
        print()
        print(json.dumps(
            {"keywords": keywords, "source": args.source,
             "stats": file_stats, "results": results},
            ensure_ascii=False, indent=1))
    elif not args.quiet:
        for r in results:
            print()
            print(f"{'─' * 62}")
            print(f"📄 {r['file']}")
            print(f"{'─' * 62}")
            for h in r["hits"]:
                print(f"  [关键词: {h['keyword']} · 第{h['line']}行]")
                # 摘录过长截断
                snip = h["snippet"]
                if len(snip) > 1500:
                    snip = snip[:1500] + "\n  ……（截断）"
                print(snip)
                print()


if __name__ == "__main__":
    main()
