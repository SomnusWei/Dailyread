#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""基于《生理学（第10版）》教材构建术语表。

术语来源：
  1) 教材自带「中英文名词对照索引」——权威、成体系
  2) 人工补充的生理学核心术语（索引可能遗漏的口语高频词）

输出：
  terms/terms.txt          纯术语列表（按长度降序）
  terms/terms_detail.tsv   术语 + 来源
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXTBOOK = r"c:\Users\somnu\.trae-cn\skills\yixue-zonghe\西医教材\生理学 （第10版）.txt"
OUTDIR = os.path.join(BASE, "terms")

CN = r"\u4e00-\u9fff"
BAD = "。！？，；：、（）()《》【】…—～~\"'“”‘’"

# 虚词/口语字（与 correct_terms.py 保持一致）
FUNC_CHARS = set(
    "的了是不在和与等这那我你他她们就都还也而且很没把被吗吧呢啊一"
    "个们么什怎为以于之其所以如果但因故虽则并且或更"
    "搞弄说讲想让给找拿走该别挺太真唱玩写念买卖"
)

# 索引条目特征：以页码（数字，可含逗号）结尾，且含拉丁/希腊字母（英文名）
ENTRY_END = re.compile(r"\d[\d,\s\-]*$")
HAS_LATIN = re.compile(r"[A-Za-z\u0370-\u03ff]")

CORE = """
静息电位 动作电位 钠钾泵 钠泵 钾漏通道 阈电位 阈强度 局部电位 电紧张电位 终板电位
兴奋-收缩耦联 肌浆网 终池 横小管 纵管 三联管 肌钙蛋白 原肌球蛋白 横桥 肌动蛋白 肌球蛋白
闰盘 快反应细胞 慢反应细胞 有效不应期 相对不应期 超常期 低常期 期前收缩 代偿间歇
血浆晶体渗透压 血浆胶体渗透压 血细胞比容 红细胞沉降率 血沉 生理性止血 血液凝固 纤维蛋白溶解
内源性凝血 外源性凝血 凝血因子 抗凝血酶 促红细胞生成素 造血干细胞 中性粒细胞 单核细胞 淋巴细胞
心动周期 每搏输出量 每分输出量 心输出量 射血分数 心指数 心力储备 异长自身调节 等长自身调节
心肌收缩能力 前负荷 后负荷 动脉血压 收缩压 舒张压 脉压 平均动脉压 中心静脉压 微循环 有效滤过压
组织液 淋巴液 压力感受性反射 颈动脉窦 主动脉弓 化学感受性反射 肾素血管紧张素系统 心肺感受器
肺活量 用力肺活量 时间肺活量 每分通气量 肺泡通气量 解剖无效腔 生理无效腔 潮气量 补吸气量 补呼气量
残气量 功能余气量 肺泡表面活性物质 肺牵张反射 肺顺应性 通气血流比值 血氧容量 血氧含量 血氧饱和度
氧解离曲线 波尔效应 二氧化碳解离曲线 氧离曲线 化学感受器 中枢化学感受器 外周化学感受器
胃液 盐酸 胃蛋白酶原 内因子 黏液碳酸氢盐屏障 胃排空 胃肠激素 促胃液素 缩胆囊素 促胰液素
胰液 胆汁 分节运动 蠕动 集团蠕动 基础代谢率 食物的热价 氧热价 呼吸商 体温调定点
肾小球滤过率 滤过分数 肾血浆流量 肾血流量 滤过膜 球管平衡 渗透性利尿 水利尿
肾糖阈 葡萄糖重吸收极限 抗利尿激素 醛固酮 心房钠尿肽 髓质高渗 逆流倍增 逆流交换
突触传递 突触后电位 兴奋性突触后电位 抑制性突触后电位 突触前抑制 突触后抑制 突触前易化
神经递质 调质 第二信使 特异性投射系统 非特异性投射系统 感觉柱 感受器电位 感受器的适应
牵涉痛 牵张反射 腱反射 肌紧张 反牵张反射 脊休克 屈肌反射 对侧伸肌反射 状态反射 翻正反射
交感神经 副交感神经 自主神经系统 下丘脑 腺垂体 神经垂体 生长激素 甲状腺激素 甲状旁腺激素
降钙素 糖皮质激素 盐皮质激素 肾上腺素 去甲肾上腺素 胰岛素 胰高血糖素 月经周期
排卵 着床 精子获能 顶体反应 兴奋性 传导性 收缩性 自律性 自动节律性 内皮素 组胺 激肽
内环境 稳态 正反馈 负反馈 前馈 自身调节 神经调节 体液调节 免疫调节 单纯扩散 易化扩散
原发性主动转运 继发性主动转运 出胞 入胞 胞吞 胞吐 钠-葡萄糖同向转运体 钠钙交换体
离子通道型受体 酪氨酸激酶受体 核受体 跨膜信号转导 信号转导 静息张力 肌小节
心律失常 心肌梗死 心肌缺血 心绞痛 冠心病 动脉粥样硬化 心力衰竭 呼吸衰竭 肾功能衰竭
高血压 低血压 休克 水肿 贫血 发热 缺氧 酸中毒 碱中毒 尿毒症 甲状腺功能亢进 甲状腺功能减退
糖尿病 动脉硬化 血栓形成 出血 炎症 肿痛 感染 过敏 肝硬化 胃炎 胃溃疡 肺炎 哮喘 肺结核
肾炎 肾小球肾炎 关节炎 骨质疏松 癫痫 帕金森病 阿尔茨海默病
""".split()


def looks_like_entry(line: str) -> bool:
    return bool(ENTRY_END.search(line) and HAS_LATIN.search(line))


def find_index_start(lines):
    """定位真正的索引区起点：该行后连续条目占比高。"""
    cands = [i for i, l in enumerate(lines) if "中英文名词对照索引" in l]
    best = None
    for i in cands:
        window = [l.strip() for l in lines[i + 1:i + 31] if l.strip()]
        if len(window) < 10:
            continue
        ratio = sum(1 for l in window if looks_like_entry(l)) / len(window)
        if ratio >= 0.6:
            best = i
            break
    return best


def extract_index_terms(lines, start):
    """把索引区拼成整段文本后用正则抽取，可覆盖「英文名换行」的条目。"""
    block = " ".join(l.strip() for l in lines[start:])
    block = re.sub(r"[\u3000]+", " ", block)
    # 术语（中文字开头，可含字母数字） + 英文名 + 页码
    pat = re.compile(
        r"([\u4e00-\u9fff][\u4e00-\u9fffA-Za-z0-9·\-\+]{1,15}?)\s+"
        r"([A-Za-z\u0370-\u03ff][A-Za-z\u0370-\u03ff\s\-/,\.0-9+\(\)]{2,70}?)\s+"
        r"(\d[\d,\s]*)"
    )
    terms = {}
    for m in pat.finditer(block):
        cand = re.sub(r"[\s\u3000]+", "", m.group(1)).strip("·-、,，+")
        if not cand or not (2 <= len(cand) <= 16):
            continue
        if any(ch in BAD for ch in cand):
            continue
        n_cn = len(re.findall(f"[{CN}]", cand))
        if n_cn < 1 or n_cn < len(cand) * 0.5:
            continue
        terms[cand] = "教材索引"
    return terms


def harvest_body_terms(text: str, min_count: int = 5000):
    """从教材正文按词频收割术语（补齐索引未收录的章节名、疾病名等）。

    规则：中文 3–7 字连续片段，出现 ≥ min_count 次，且不含虚词/口语字。
    """
    body = re.sub(r"[^\u4e00-\u9fff]", " ", text)
    counts = {}
    for seg in body.split():
        n = len(seg)
        if n < 3:
            continue
        for size in range(3, min(7, n) + 1):
            for i in range(0, n - size + 1):
                ng = seg[i:i + size]
                if any(ch in FUNC_CHARS for ch in ng):
                    continue
                counts[ng] = counts.get(ng, 0) + 1
    return {k for k, v in counts.items() if v >= min_count}


def main():
    if not os.path.exists(TEXTBOOK):
        print("教材不存在:", TEXTBOOK)
        return 1
    lines = open(TEXTBOOK, encoding="utf-8", errors="ignore").read().splitlines()
    start = find_index_start(lines)
    print("总行数:", len(lines), "| 索引区起点: 第", (start + 1) if start is not None else None, "行")
    terms = extract_index_terms(lines, start) if start is not None else {}
    print("索引提取术语:", len(terms))
    body_terms = harvest_body_terms("\n".join(lines))
    added_body = 0
    for t in body_terms:
        if t not in terms:
            terms[t] = "教材正文"
            added_body += 1
    print("正文收割术语:", len(body_terms), "| 新增:", added_body)
    core = 0
    for t in CORE:
        if t and t not in terms:
            terms[t] = "人工补充"
            core += 1
    print("人工补充:", core, "| 合计:", len(terms))

    os.makedirs(OUTDIR, exist_ok=True)
    lst = sorted(terms.keys(), key=lambda x: (-len(x), x))
    with open(os.path.join(OUTDIR, "terms.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lst))
    with open(os.path.join(OUTDIR, "terms_detail.tsv"), "w", encoding="utf-8") as f:
        for t in lst:
            f.write(f"{t}\t{terms[t]}\n")
    print("已写出:", os.path.join(OUTDIR, "terms.txt"))
    print("长术语样例:", [t for t in lst if len(t) >= 5][:12])
    print("短术语样例:", [t for t in lst if len(t) == 3][:12])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
