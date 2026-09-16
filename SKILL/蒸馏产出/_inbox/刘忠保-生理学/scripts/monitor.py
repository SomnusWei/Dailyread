#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""里程碑播报：等待「已完成集数」达到目标值（每 5 集一档），输出进度报告。

用法：
    python monitor.py 10            # 等到累计完成 10 集（P1–P5 计入）
    python monitor.py 15 --timeout-min 90

行为：
    - 每 60 秒轮询 manifest.json
    - 达到目标或超时后打印报告，并追加写入 logs/progress_milestones.md
"""
import argparse
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
EPS = os.path.join(INBOX, "episodes.json")
MAN = os.path.join(INBOX, "manifest.json")
MILESTONE_LOG = os.path.join(INBOX, "logs", "progress_milestones.md")
BATCH_START = 6  # 全量批次起始集号


def snapshot():
    eps = {e["index"]: e for e in json.load(open(EPS, encoding="utf-8"))}
    man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}
    done = sorted(int(k) for k, v in man.items() if v.get("state") == "done")
    failed = sorted(int(k) for k, v in man.items() if v.get("state") == "failed")
    batch = [i for i in done if i >= BATCH_START]
    tot_all = sum(e["duration"] for e in eps.values())
    tot_done = sum(eps[i]["duration"] for i in done if i in eps)
    el = sum(man[str(i)].get("elapsed", 0) for i in batch)
    dur = sum(man[str(i)].get("dur", 0) for i in batch)
    rtf = (el / dur) if dur else 0.10
    remain_h = (tot_all - tot_done) / 3600
    return dict(eps=eps, man=man, done=done, failed=failed, batch=batch,
                tot_all=tot_all, tot_done=tot_done, rtf=rtf, remain_h=remain_h,
                chars=sum(v.get("chars", 0) for v in man.values()),
                corr=sum(v.get("corr", 0) for v in man.values()),
                pend=sum(v.get("pend", 0) for v in man.values()))


def report(s, target):
    eta = time.localtime(time.time() + s["remain_h"] * 3600 * s["rtf"] + 300)
    lines = []
    lines.append(f"\n### 里程碑：累计完成 {len(s['done'])} 集（目标 {target}）\n")
    lines.append(f"- 全量批次已完成：{len(s['batch'])} 集 {s['batch']}\n")
    lines.append(f"- 音频进度：{s['tot_done']/3600:.2f} h / {s['tot_all']/3600:.2f} h"
                 f"（剩余 {s['remain_h']:.2f} h）\n")
    lines.append(f"- 实测 RTF：{s['rtf']:.4f} → 预计完成 {time.strftime('%Y-%m-%d %H:%M', eta)}\n")
    lines.append(f"- 累计字数 {s['chars']:,} | 纠错 {s['corr']} 处 | 待复核 {s['pend']} 处\n")
    if s["failed"]:
        lines.append(f"- ⚠️ 失败集号：{s['failed']}\n")
    txt = "".join(lines)
    print(txt, flush=True)
    with open(MILESTONE_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n## {time.strftime('%Y-%m-%d %H:%M:%S')}\n{txt}")
    return txt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target", type=int)
    ap.add_argument("--timeout-min", type=float, default=120)
    a = ap.parse_args()
    t0 = time.time()
    while True:
        s = snapshot()
        if len(s["done"]) >= a.target:
            report(s, a.target)
            return 0
        if (time.time() - t0) / 60 > a.timeout_min:
            print(f"⏱ 超时（{a.timeout_min} 分钟）仍未达到目标 {a.target} 集；"
                  f"当前完成 {len(s['done'])} 集")
            report(s, a.target)
            return 1
        cur = s["batch"][-1] if s["batch"] else BATCH_START
        print(f"  等待中… 已完成 {len(s['done'])} 集（最新 P{cur:02d}）", flush=True)
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
