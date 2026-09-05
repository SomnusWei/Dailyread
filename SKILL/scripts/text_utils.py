#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中医知识库文本读取工具（共享模块）

教材目录编码现状（2026-09 校验，711 个 txt）：
  - 10 部现代教材: UTF-8
  - 701 部古籍（GitHub TCM-Ancient-Books）: GB18030（GBK 超集）
  - 1 部（203-婴童类萃.txt）: GB18030 + 个别损坏字节，需容错解码

用法（其他脚本）：
  from text_utils import read_text_lines, read_text, detect_encoding
"""

import os

# 编码探测顺序：严格 UTF-8 → 严格 GB18030 → 容错 GB18030
_CANDIDATE_ENCODINGS = ("utf-8", "gb18030")


def detect_encoding(path):
    """探测文件编码，返回编码名；无法确定时返回 'gb18030'（容错兜底）"""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return "utf-8"
    for enc in _CANDIDATE_ENCODINGS:
        try:
            data.decode(enc)
            return enc
        except (UnicodeDecodeError, ValueError):
            continue
    return "gb18030"  # 含损坏字节，交给调用方容错


def read_text(path, errors="strict"):
    """读取整个文件文本，自动处理 UTF-8 / GB18030 编码。

    errors='strict'（默认）：损坏字节会抛 UnicodeDecodeError
    errors='replace'      ：损坏字节替换为 �，保证不中断
    """
    enc = detect_encoding(path)
    if errors != "strict":
        enc = enc if enc in _CANDIDATE_ENCODINGS else "gb18030"
        with open(path, "r", encoding=enc, errors=errors) as f:
            return f.read()
    try:
        with open(path, "r", encoding=enc) as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="gb18030", errors="replace") as f:
            return f.read()


def read_text_lines(path):
    """读取文件为行列表（保留换行符），自动编码检测 + 容错。"""
    return read_text(path, errors="replace").splitlines(keepends=True)


def clean_ancient_markup(text):
    """清理古籍文本标记：<篇名>/<目录>/属性：/\r"""
    text = text.replace("<篇名>", "【篇】").replace("<目录>", "【目录】")
    text = text.replace("属性：", "")
    return text.replace("\r", "")


if __name__ == "__main__":
    # 自检：对目录下所有 txt 做编码探测
    import sys
    import collections
    directory = sys.argv[1] if len(sys.argv) > 1 else r"F:\work\中医学skill\教材"
    stats = collections.Counter()
    for fname in sorted(os.listdir(directory)):
        if not fname.lower().endswith(".txt"):
            continue
        enc = detect_encoding(os.path.join(directory, fname))
        stats[enc] += 1
    for enc, n in stats.most_common():
        print(f"{enc}: {n} 个文件")
