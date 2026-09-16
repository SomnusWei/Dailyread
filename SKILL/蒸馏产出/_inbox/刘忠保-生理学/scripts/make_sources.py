#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成仓颉蒸馏 Step 2 的素材清单 01-sources.md（来源清单 + 可信度标注）。

素材构成：
  一手 A：B 站《生理学本科教学及考研基础课》73 集课堂实录（本任务转写）
  一手 B：《生理学（第10版）》人卫教材（术语纠错基线与交叉验证基线）
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.dirname(BASE)
OUT = os.path.join(INBOX, "distill", "references", "research", "01-sources.md")

EPS = os.path.join(INBOX, "episodes.json")
MAN = os.path.join(INBOX, "manifest.json")

# 生理学 12 章与集号区段的人工映射（依分P标题归纳）
SECTIONS = [
    ("绪论", "P1"),
    ("细胞的基本功能", "P2–P12"),
    ("血液", "P13–P19"),
    ("血液循环", "P20–P33"),
    ("呼吸", "P34–P40"),
    ("消化与吸收", "P41–P46"),
    ("能量代谢与体温", "P47–P50"),
    ("尿的生成和排出", "P51–P56"),
    ("感觉器官的功能", "P57–P59"),
    ("神经系统的功能", "P60–P66"),
    ("内分泌", "P67–P71"),
    ("生殖", "P72–P73"),
]


def main():
    eps = json.load(open(EPS, encoding="utf-8"))
    man = json.load(open(MAN, encoding="utf-8")) if os.path.exists(MAN) else {}
    done = [e for e in eps if man.get(str(e["index"]), {}).get("state") == "done"]
    total_h = sum(e["duration"] for e in eps) / 3600
    chars = sum(man.get(str(e["index"]), {}).get("chars", 0) for e in eps)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    L = []
    L.append("# 01 · 来源清单（刘忠保《生理学》专家库）\n")
    L.append("> 蒸馏类型：**C 类 · 视频课程蒸馏**（仓颉 A 类人物 / B 类教材之外的适配型）\n")
    L.append("> 生成方式：`scripts/make_sources.py` 自动生成，转写进度变化后可重跑覆盖。\n")
    L.append("\n## 一、素材总览\n")
    L.append("| 编号 | 素材 | 形态 | 体量 | 一手/二手 | 可信度 | 用途 |")
    L.append("|------|------|------|------|----------|--------|------|")
    L.append(f"| A | B 站《生理学本科教学及考研基础课》（UP 主：医学老师刘忠保，BV1va4y1J72r）"
             f" | 视频 73 集，本任务转写为带时间戳文本 | {total_h:.2f} 小时音频；"
             f"已转写 {len(done)} 集 / {chars:,} 字 | **一手**（本人授课原声） | ★★★ 高（原声直录，仅存 ASR 误识风险，已术语纠错）"
             f" | L1–L7 全部提取来源 |")
    L.append("| B | 《生理学（第10版）》（人民卫生出版社） | PDF + 抽取文本 1.6 MB（60 万字） | 全书 12 章 | "
             "**一手**（学科权威基线） | ★★★ 高（教材原文） | 术语纠错词表（1,191 条）、章节对齐坐标、知识交叉验证 |")
    L.append("| C | 教材「中英文名词对照索引」 | 索引条目 1,053 条 | — | 一手（教材附录） | ★★★ 高 | 术语标准写法校验 |")
    L.append("| D | WebSearch 外部素材（访谈/课程介绍/讲义前言） | 待补充 | — | 二手 | ★★ 中 | "
             "补 L2（个人经历决策）与 L3（自我修正）维度；**不足则如实标注「素材不足」** |")
    L.append("\n## 二、转写与纠错流水线（A 素材的加工过程）\n")
    L.append("| 环节 | 实现 | 质量记录 |")
    L.append("|------|------|----------|")
    L.append("| 音频抓取 | yt-dlp，仅抽音频（m4a），逐集下载、转写完即处理 | 峰值 33 MB/s，无需 cookies |")
    L.append("| 语音识别 | faster-whisper large-v3（CUDA / int8_float16 / beam 1 / 逐段推理） | "
             "5 集实测 RTF 0.1004（约 10 倍实时）；全量 67.32 h 预计约 6.8 h |")
    L.append("| 术语纠错 | 教材术语表 1,191 条 × 教材全文 60 万字 × 模糊拼音匹配；"
             "三道护栏：虚词黑名单、自洽性校验、上下文护栏 | 抽样 5 集纠错清单全部为真实误识；"
             "两处概念性误纠（单向转运/蛋白消）已修复并复核 |")
    L.append("| 时间戳 | 每句 `[hh:mm:ss]` | 全部结论可回溯到分钟级原话 |")
    L.append("\n**已知局限（须在 SKILL.md 认知边界中声明）**：\n")
    L.append("1. **二字词同音未纠**（如「续论」应为「绪论」）：算法下限为 3 字（二字放开经实测会引发大量误纠）\n")
    L.append("2. **夹杂英文术语易被汉语化误识**（如 physiology → 「非自二者」）：此类处标注存疑，不据此下结论\n")
    L.append("3. **ASR 断句与口语重复**：课堂口语存在冗余与重复，提取时以语义为准，不逐字直引长句\n")
    L.append("\n## 三、素材覆盖度（按生理学 12 章）\n")
    L.append("| 章 | 集号区段 | 状态 |")
    L.append("|----|----------|------|")
    for name, rng in SECTIONS:
        L.append(f"| {name} | {rng} | 见下方分集表 |")
    L.append("\n## 四、分集清单（73 集）\n")
    L.append("| 集号 | 标题 | 时长 | 转写字数 | 分段 | 已纠错 | 待复核 | 状态 |")
    L.append("|------|------|------|----------|------|--------|--------|------|")
    for e in eps:
        i = str(e["index"])
        m = man.get(i, {})
        d = e["duration"]
        L.append(f"| P{e['index']:02d} | {e['title']} | {d//60}分{d%60}秒 | "
                 f"{m.get('chars', '—')} | {m.get('segs', '—')} | {m.get('corr', '—')} | "
                 f"{m.get('pend', '—')} | {m.get('state', '待处理')} |")
    L.append("\n## 五、合规与使用边界\n")
    L.append("- 转写文本**仅用于个人学习与研究**，本地保存，不对外传播、不商用、不再分发\n")
    L.append("- 音频仅本地留档；著作权归原作者「医学老师刘忠保」及发布平台所有\n")
    L.append("- 生成专家库中的一切观点均标注来源与时间戳，**不代表原作者立场**，也不替代教材结论\n")
    L.append("- 若权利人提出异议，立即停止并删除全部衍生文本\n")

    open(OUT, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("已生成:", OUT)
    print(f"素材：{len(eps)} 集 / {total_h:.2f} h；已转写 {len(done)} 集 / {chars:,} 字")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
