#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""最终装机：刷新调研文件 → 质检（须 11/11）→ 安装到蒸馏产出 → 检索接入验证。

用法：
    python finalize.py            # 全流程
    python finalize.py --check    # 只跑质检
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
# INBOX = <skill>/蒸馏产出/_inbox/刘忠保-生理学 → 上退三级得到 skill 根目录
SKILL_ROOT = os.path.abspath(os.path.join(INBOX, "..", "..", ".."))
PY = r"C:\Users\somnu\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
DISTILL = os.path.join(INBOX, "distill")
TARGET = os.path.join(SKILL_ROOT, "蒸馏产出", "刘忠保-生理学-perspective")


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="ignore", **kw)


def step(title):
    print("\n" + "=" * 64)
    print(f"▶ {title}")
    print("=" * 64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只跑质检")
    a = ap.parse_args()

    if not a.check:
        # 1) 刷新调研文件
        step("1/5 刷新调研文件（来源清单 + 知识地图）")
        for s in ("make_sources.py", "build_knowledge_map.py"):
            r = run([PY, os.path.join(BASE, s)])
            print((r.stdout or "").strip()[-400:])

    # 2) 质检
    step("2/5 质检（仓颉 11 项，须全部通过）")
    skill_md = os.path.join(DISTILL, "SKILL.md")
    r = run([PY, os.path.join(SKILL_ROOT, "仓颉", "scripts", "quality_check.py"), skill_md])
    print(r.stdout)
    if r.returncode != 0:
        print("❌ 质检未达 11/11，停止安装")
        if r.stderr:
            print("--- stderr ---")
            print(r.stderr[:1500])
        return 1
    if a.check:
        return 0

    # 3) 安装
    step("3/5 安装到 " + TARGET)
    if os.path.exists(TARGET):
        shutil.rmtree(TARGET)
    os.makedirs(TARGET)
    shutil.copy2(skill_md, os.path.join(TARGET, "SKILL.md"))
    src_ref = os.path.join(DISTILL, "references")
    dst_ref = os.path.join(TARGET, "references")
    if os.path.isdir(src_ref):
        shutil.copytree(src_ref, dst_ref)
    if os.path.exists(os.path.join(DISTILL, "ASSEMBLY-NOTES.md")):
        shutil.copy2(os.path.join(DISTILL, "ASSEMBLY-NOTES.md"),
                     os.path.join(TARGET, "ASSEMBLY-NOTES.md"))
    n = sum(len(f) for _, _, f in os.walk(TARGET))
    print(f"✅ 已安装，共 {n} 个文件")
    for dp, _, fs in os.walk(TARGET):
        for f in fs:
            print("   ", os.path.relpath(os.path.join(dp, f), TARGET))

    # 4) 体系判定自检
    step("4/5 专家体系判定自检（应判为「西医」）")
    sys.path.insert(0, os.path.join(SKILL_ROOT, "scripts"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "st", os.path.join(SKILL_ROOT, "scripts", "search_textbooks.py"))
        st = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(st)
        print("判定结果：", st._expert_track(TARGET))
    except Exception as e:
        print("判定自检跳过：", e)

    # 5) 检索接入验证
    step("5/5 检索接入验证（西医 track 应命中该专家）")
    r = run([PY, os.path.join(SKILL_ROOT, "scripts", "search_textbooks.py"),
             "--track", "西医", "--keyword", "动作电位", "--quiet", "--max-hits", "1"])
    out = r.stdout or ""
    hit = "刘忠保-生理学-perspective" in out
    print(out[:1200])
    print(("✅ 接入成功：西医检索已命中该专家" if hit
           else "⚠️ 未在命中列表中看到该专家，请检查关键词覆盖"))
    return 0 if hit else 2


if __name__ == "__main__":
    raise SystemExit(main())
