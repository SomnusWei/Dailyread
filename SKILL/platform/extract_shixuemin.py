# -*- coding: utf-8 -*-
"""
石学敏针灸全集 · PDF 文本抽取（幂等）

把 `石学敏体系/石学敏针灸全集 第2版.pdf`（约 207MB）按 100 页分卷抽取为文本，
输出到 `石学敏体系/针灸全集/`：
    卷01-页0001-0100.txt … 卷11-页1001-1071.txt
    全文.txt
    00-目录.md

已存在且非空的 `全文.txt` 时直接退出（幂等）。
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT_DIR = os.path.join(SKILL_ROOT, "石学敏体系", "针灸全集")
PDF_CANDIDATES = [
    os.path.join(SKILL_ROOT, "石学敏体系", "石学敏针灸全集 第2版.pdf"),
    os.path.join(SKILL_ROOT, "石学敏体系", "石学敏针灸全集_第2版.pdf"),
]
PAGES_PER_VOLUME = 100


def find_pdf():
    for p in PDF_CANDIDATES:
        if os.path.isfile(p):
            return p
    # 退化为目录内首个 pdf
    d = os.path.join(SKILL_ROOT, "石学敏体系")
    if os.path.isdir(d):
        for fn in sorted(os.listdir(d)):
            if fn.lower().endswith(".pdf"):
                return os.path.join(d, fn)
    return None


def main():
    full_txt = os.path.join(OUT_DIR, "全文.txt")
    if os.path.isfile(full_txt) and os.path.getsize(full_txt) > 1024:
        print(f"✅ 已抽取过，跳过（{full_txt}）")
        return 0

    pdf = find_pdf()
    if not pdf:
        print("❌ 未找到石学敏针灸全集 PDF")
        return 1

    try:
        sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
        from text_utils import _open_fitz  # noqa
        fitz = _open_fitz()
    except Exception as e:
        print(f"❌ 无法加载 PyMuPDF: {e}")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    print(f"📖 打开 PDF: {os.path.basename(pdf)}（{os.path.getsize(pdf)/1048576:.1f}MB）")

    doc = fitz.open(pdf)
    total = doc.page_count
    print(f"共 {total} 页，按 {PAGES_PER_VOLUME} 页分卷…")

    all_pages = []
    for i in range(total):
        all_pages.append(doc[i].get_text("text") or "")
    doc.close()

    volumes = []
    for start in range(0, total, PAGES_PER_VOLUME):
        end = min(start + PAGES_PER_VOLUME, total)
        idx = start // PAGES_PER_VOLUME + 1
        fname = f"卷{idx:02d}-页{start+1:04d}-{end:04d}.txt"
        fpath = os.path.join(OUT_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            for p in range(start, end):
                f.write(f"\n\n===== 第 {p+1} 页 =====\n")
                f.write(all_pages[p])
        volumes.append((fname, end - start, os.path.getsize(fpath)))
        print(f"  ✅ {fname}（{end-start} 页，{os.path.getsize(fpath)/1024:.0f}KB）")

    with open(full_txt, "w", encoding="utf-8") as f:
        for p, txt in enumerate(all_pages):
            f.write(f"\n\n===== 第 {p+1} 页 =====\n")
            f.write(txt)

    with open(os.path.join(OUT_DIR, "00-目录.md"), "w", encoding="utf-8") as f:
        f.write("# 石学敏针灸全集（第 2 版）· 分卷目录\n\n")
        f.write(f"> 源文件：`{os.path.basename(pdf)}` ｜ 共 {total} 页 ｜ "
                f"抽取于 {time.strftime('%Y-%m-%d %H:%M')}\n\n")
        f.write("| 分卷 | 页范围 | 大小 |\n|------|--------|------|\n")
        for i, (fname, n, size) in enumerate(volumes, 1):
            start = (i - 1) * PAGES_PER_VOLUME + 1
            f.write(f"| `{fname}` | {start}-{start+n-1} | {size/1024:.0f}KB |\n")
        f.write(f"\n全文合并：`全文.txt`（{os.path.getsize(full_txt)/1048576:.1f}MB）\n")

    chars = sum(len(t) for t in all_pages)
    print("-" * 56)
    print(f"✅ 抽取完成：{len(volumes)} 卷 / {total} 页 / {chars} 字符 "
          f"/ 耗时 {time.time()-t0:.1f}s")
    print(f"   输出目录：{OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
