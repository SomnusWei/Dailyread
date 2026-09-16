#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""刘忠保《生理学》课程音频转写（faster-whisper large-v3 / CUDA）

用法：
    python transcribe.py <音频文件> <输出txt> [起始秒] [持续秒]
环境变量：
    HF_ENDPOINT      模型下载镜像，默认 https://hf-mirror.com
    WHISPER_MODEL    默认 large-v3
    WHISPER_DEVICE   默认 cuda，失败可设 cpu
    WHISPER_COMPUTE  默认 float16（cpu 时用 int8）
    WHISPER_CACHE    模型缓存目录
    WHISPER_BATCH    批大小，默认 8（8G 显存建议 8）
"""
import os
import site
import sys
import time

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


def _add_cuda_dlls():
    """Windows 下 ctranslate2 不自带 CUDA 运行库，需把 pip 的 nvidia 包目录加入 DLL 搜索路径。"""
    dirs = []
    for base in list(site.getsitepackages()) + [site.getusersitepackages()]:
        for pkg in ("cublas", "cudnn", "cuda_nvrtc", "cuda_runtime"):
            p = os.path.join(base, "nvidia", pkg, "bin")
            if os.path.isdir(p):
                dirs.append(p)
    for d in dirs:
        try:
            os.add_dll_directory(d)
        except (AttributeError, OSError):
            pass
        os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
    if dirs:
        print(f"[env] 已注入 CUDA DLL 路径 {len(dirs)} 个", flush=True)
    return dirs


_add_cuda_dlls()

from faster_whisper import WhisperModel  # noqa: E402

# 生理学核心术语提示词：大幅降低专有名词误识率
INITIAL_PROMPT = (
    "以下是医学专业课程《生理学》的课堂录音，讲授内容包括：细胞的基本功能、"
    "跨膜转运、静息电位、动作电位、钠钾泵、钠泵、阈电位、兴奋性、传导性、"
    "血液、血浆渗透压、红细胞、白细胞、血小板、生理性止血、血液循环、"
    "心动周期、心输出量、血压、呼吸、肺通气、肺泡表面活性物质、"
    "消化与吸收、能量代谢、体温、尿的生成与排出、肾小球滤过率、"
    "感受器、神经系统、突触传递、神经递质、内分泌、激素、生殖。"
)


def fmt(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"[{h:02d}:{m:02d}:{s:02d}]"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    audio, out = sys.argv[1], sys.argv[2]
    offset = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
    limit = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0

    model_size = os.environ.get("WHISPER_MODEL", "large-v3")
    device = os.environ.get("WHISPER_DEVICE", "cuda")
    compute = os.environ.get("WHISPER_COMPUTE", "float16" if device == "cuda" else "int8")
    cache = os.environ.get("WHISPER_CACHE") or None
    batch = int(os.environ.get("WHISPER_BATCH", "8"))

    t0 = time.time()
    print(f"[load] {model_size} device={device} compute={compute}", flush=True)
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute,
                             download_root=cache, num_workers=1)
    except Exception as e:
        print(f"[load] {device} 加载失败（{type(e).__name__}: {e}），回退 CPU/int8", flush=True)
        device, compute = "cpu", "int8"
        model = WhisperModel(model_size, device=device, compute_type=compute,
                             download_root=cache, num_workers=1)
    print(f"[load] 完成 {time.time() - t0:.1f}s", flush=True)

    t1 = time.time()
    common = dict(
        language="zh",
        beam_size=int(os.environ.get("WHISPER_BEAM", "5")),
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400),
        initial_prompt=INITIAL_PROMPT,
        condition_on_previous_text=True,
    )
    # 支持片段试跑：offset 起始秒，limit 持续秒（clip_timestamps 语义为各片段起点列表）
    if limit:
        common["clip_timestamps"] = f"{int(offset)},{int(offset + limit)}"
    elif offset:
        common["clip_timestamps"] = str(int(offset))
    # 批处理推理管道（GPU 提速数倍）；片段模式或 WHISPER_SEQ=1 时走逐段推理
    if os.environ.get("WHISPER_SEQ") == "1":
        print("[info] 按 WHISPER_SEQ=1 使用逐段推理", flush=True)
        segments, info = model.transcribe(audio, **common)
    else:
        try:
            from faster_whisper import BatchedInferencePipeline

            pipe = BatchedInferencePipeline(model=model)
            segments, info = pipe.transcribe(audio, batch_size=batch, **common)
        except Exception as e:
            print(f"[warn] 批处理不可用（{type(e).__name__}: {e}），回退逐段推理", flush=True)
            common.pop("clip_timestamps", None)
            segments, info = model.transcribe(audio, **common)
    dur = info.duration
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    n = 0
    chars = 0
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# 源音频：{os.path.basename(audio)}\n")
        f.write(f"# 时长：{dur:.0f}s | 模型：{model_size} | {device}/{compute} | 语种：{info.language}(p={info.language_probability:.2f})\n\n")
        for seg in segments:
            n += 1
            txt = seg.text.strip()
            chars += len(txt)
            f.write(f"{fmt(seg.start)} {txt}\n")
            if n % 50 == 0:
                print(f"  seg={n} pos={seg.end:.0f}s elapsed={time.time() - t1:.0f}s", flush=True)
    el = time.time() - t1
    dur_rtf = limit if limit else dur
    rtf = el / dur_rtf if dur_rtf else 0
    print(f"[done] 音频{dur:.0f}s 分段{n} 字数{chars} 耗时{el:.0f}s RTF={rtf:.4f} "
          f"预计全量67.3h耗时={67.3 * rtf:.1f}h", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
