#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""刘忠保《生理学》全量流水线：下载 → 转写 → 纠错 → 台账（支持断点续跑）。

用法：
    python run_all.py 3 4 5            # 处理 P3~P5
    python run_all.py 1-73             # 处理全部
    python run_all.py 1-73 --keep-audio  # 保留音频（默认转写完即删）
    python run_all.py 6-73 --force      # 强制重跑（忽略已完成）

产物：
    audio/                    音频（默认转写后删除）
    transcripts_raw/PNN_标题.raw.txt
    transcripts_fixed/PNN_标题.fixed.txt  (+ _corrections.tsv / _pending_review.tsv)
    logs/run_all.log          总日志
    logs/ep_PNN.log           单集日志
    manifest.json             台账（状态/时长/字数/耗时/RTF/纠错数）
    summary.csv               台账导出
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
PY = r"C:\Users\somnu\.workbuddy\binaries\python\envs\default\Scripts\python.exe"
MODEL = r"C:\Users\somnu\.cache\fw-large-v3"
BV = "BV1va4y1J72r"

AUDIO = os.path.join(INBOX, "audio")
RAW = os.path.join(INBOX, "transcripts_raw")
FIXED = os.path.join(INBOX, "transcripts_fixed")
LOGS = os.path.join(INBOX, "logs")
MANIFEST = os.path.join(INBOX, "manifest.json")
EPISODES = os.path.join(INBOX, "episodes.json")

for d in (AUDIO, RAW, FIXED, LOGS):
    os.makedirs(d, exist_ok=True)


def log(msg: str, fp=None):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with open(os.path.join(LOGS, "run_all.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")
    if fp:
        with open(fp, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST, encoding="utf-8"))
    return {}


def save_manifest(m):
    json.dump(m, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(INBOX, "summary.csv"), "w", encoding="utf-8-sig") as f:
        f.write("集号,标题,音频秒,转写秒,RTF,字数,分段,纠错,待复核,状态,备注\n")
        for k in sorted(m, key=lambda x: int(x)):
            v = m[k]
            f.write(f"{k},{v.get('title','')},{v.get('dur',0)},{v.get('elapsed',0)},"
                    f"{v.get('rtf',0):.4f},{v.get('chars',0)},{v.get('segs',0)},"
                    f"{v.get('corr',0)},{v.get('pend',0)},{v.get('state','')},{v.get('note','')}\n")


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()


def download(i: int, title: str) -> str | None:
    """下载单集音频，返回文件路径。"""
    for f in os.listdir(AUDIO):
        if f.startswith(f"P{i:02d}") and not f.endswith(".part"):
            return os.path.join(AUDIO, f)
    cmd = [PY, "-m", "yt_dlp", "-I", str(i),
           "-f", "bestaudio[ext=m4a]/bestaudio/best", "--retries", "5", "--no-overwrites",
           "-o", os.path.join(AUDIO, f"P{i:02d}-%(title)s.%(ext)s"),
           f"https://www.bilibili.com/video/{BV}"]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")
    if r.returncode != 0:
        return None
    for f in os.listdir(AUDIO):
        if f.startswith(f"P{i:02d}") and not f.endswith(".part"):
            return os.path.join(AUDIO, f)
    return None


def run_episode(i: int, ep: dict, keep_audio=False):
    title = safe(ep["title"]) or f"P{i:02d}"
    stem = f"P{i:02d}_{title}"
    tlog = os.path.join(LOGS, f"ep_P{i:02d}.log")
    if os.path.exists(tlog):
        os.remove(tlog)
    rec = {"title": title, "dur": ep["duration"], "state": "running", "note": ""}

    # 1) 下载
    log(f"P{i:02d} [{title}] 下载音频…", tlog)
    audio = download(i, title)
    if not audio:
        log(f"P{i:02d} 下载失败", tlog)
        rec.update(state="failed", note="download")
        return rec
    log(f"P{i:02d} 音频 {os.path.getsize(audio)/1048576:.1f} MB", tlog)

    # 2) 转写
    env = dict(os.environ)
    env.update({"WHISPER_MODEL": MODEL, "WHISPER_DEVICE": "cuda",
                "WHISPER_COMPUTE": "int8_float16", "WHISPER_BEAM": "1", "WHISPER_SEQ": "1"})
    raw_out = os.path.join(RAW, stem + ".raw.txt")
    ok = False
    for attempt in (1, 2):
        log(f"P{i:02d} 转写（第 {attempt} 次）…", tlog)
        with open(tlog, "a", encoding="utf-8") as f:
            r = subprocess.run([PY, os.path.join(BASE, "transcribe.py"), audio, raw_out],
                               stdout=f, stderr=subprocess.STDOUT, env=env)
        if r.returncode == 0 and os.path.exists(raw_out):
            ok = True
            break
        if attempt == 1:
            env["WHISPER_DEVICE"] = "cpu"
            env["WHISPER_COMPUTE"] = "int8"
            log(f"P{i:02d} 转写失败，回退 CPU 重试", tlog)
    if not ok:
        log(f"P{i:02d} 转写失败（两次）", tlog)
        rec.update(state="failed", note="transcribe")
        return rec

    txt = open(tlog, encoding="utf-8", errors="ignore").read()
    m = re.search(r"\[done\] 音频(\d+)s 分段(\d+) 字数(\d+) 耗时(\d+)s RTF=([\d.]+)", txt)
    if m:
        rec.update(dur=int(m.group(1)), segs=int(m.group(2)), chars=int(m.group(3)),
                   elapsed=int(m.group(4)), rtf=float(m.group(5)))

    # 3) 纠错
    log(f"P{i:02d} 术语纠错…", tlog)
    fixed_out = os.path.join(FIXED, stem + ".fixed.txt")
    with open(tlog, "a", encoding="utf-8") as f:
        subprocess.run([PY, os.path.join(BASE, "correct_terms.py"), raw_out, fixed_out],
                       stdout=f, stderr=subprocess.STDOUT)
    txt = open(tlog, encoding="utf-8", errors="ignore").read()
    mc = re.search(r"已应用纠错 (\d+) 处（high (\d+) / medium (\d+)）", txt)
    mp = re.search(r"待复核（未改写）(\d+) 处", txt)
    if mc:
        rec["corr"] = int(mc.group(1))
        rec["corr_high"] = int(mc.group(2))
        rec["corr_medium"] = int(mc.group(3))
    if mp:
        rec["pend"] = int(mp.group(1))

    # 4) 清理音频
    if not keep_audio:
        try:
            mb = os.path.getsize(audio) / 1048576
            os.remove(audio)
            log(f"P{i:02d} 音频已清理（释放 {mb:.1f} MB）", tlog)
        except OSError as e:
            log(f"P{i:02d} 音频清理失败：{e}", tlog)

    rec["state"] = "done"
    rec["fixed"] = os.path.basename(fixed_out)
    log(f"P{i:02d} 完成：{rec.get('chars',0)} 字 | 分段 {rec.get('segs',0)} | "
        f"RTF {rec.get('rtf',0):.4f} | 纠错 {rec.get('corr',0)} | 待复核 {rec.get('pend',0)}", tlog)
    return rec


def parse_range(tokens):
    idx = []
    for t in tokens:
        if "-" in t:
            a, b = t.split("-")
            idx.extend(range(int(a), int(b) + 1))
        else:
            idx.append(int(t))
    return sorted(set(idx))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    keep = "--keep-audio" in sys.argv
    force = "--force" in sys.argv
    if not args:
        print(__doc__)
        return 2
    eps = {e["index"]: e for e in json.load(open(EPISODES, encoding="utf-8"))}
    targets = parse_range(args)
    man = load_manifest()

    todo = []
    for i in targets:
        if i not in eps:
            log(f"P{i:02d} 不在合集清单中，跳过")
            continue
        prev = man.get(str(i), {})
        if not force and prev.get("state") == "done" and os.path.exists(
                os.path.join(FIXED, prev.get("fixed", ""))):
            log(f"P{i:02d} 已完成，跳过（断点续跑）")
            continue
        todo.append(i)

    total = sum(eps[i]["duration"] for i in todo)
    log(f"===== 本次待处理 {len(todo)} 集，合计 {total/3600:.2f} 小时音频：{todo} =====")
    t0 = time.time()
    for n, i in enumerate(todo, 1):
        log(f"---- [{n}/{len(todo)}] P{i:02d} {eps[i]['title']} ----")
        rec = run_episode(i, eps[i], keep)
        man[str(i)] = rec
        save_manifest(man)
    el = time.time() - t0
    done = [i for i in todo if man.get(str(i), {}).get("state") == "done"]
    fail = [i for i in todo if man.get(str(i), {}).get("state") == "failed"]
    chars = sum(man[str(i)].get("chars", 0) for i in done)
    log(f"===== 批次结束：成功 {len(done)} / 失败 {len(fail)} | 本次耗时 {el/60:.1f} 分钟 "
        f"| 新增字数 {chars} =====")
    if fail:
        log(f"失败集号：{fail}（可重跑：python run_all.py {' '.join(map(str, fail))}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
