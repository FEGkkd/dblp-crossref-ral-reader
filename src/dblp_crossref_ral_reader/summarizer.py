from __future__ import annotations

import re
from collections import Counter

from .matcher import keyword_overlap_counts
from .models import PaperRecord, SearchConfig
from .utils import (
    cut_text,
    journal_scope_label,
    normalize_requested_journals,
    normalize_title,
    unique_preserve_order,
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "toward",
    "towards",
    "using",
    "via",
    "with",
    "based",
    "letter",
    "letters",
    "ieee",
    "robotics",
    "automation",
}

METHOD_CATEGORIES = {
    "learning": (
        "reinforcement learning",
        "imitation learning",
        "learning",
        "policy",
        "neural",
        "transformer",
        "diffusion",
    ),
    "control": ("control", "mpc", "formation", "tracking", "stability"),
    "planning": ("planning", "trajectory", "path", "navigation"),
    "perception": ("vision", "perception", "camera", "lidar", "sensing"),
    "manipulation": ("grasp", "manipulation", "assembly", "hand"),
    "locomotion": ("legged", "locomotion", "walking", "quadruped"),
    "multi-robot": ("multi-robot", "swarm", "multi-uav", "multi-agent", "formation control"),
}

TRANSLATION_RULES = [
    ("unmanned aerial vehicles", "无人机"),
    ("unmanned aerial vehicle", "无人机"),
    ("multi-uav", "多无人机"),
    ("multi robot", "多机器人"),
    ("large-scale", "大规模"),
    ("real-time", "实时"),
    ("frontier-based", "基于前沿的"),
    ("coverage path guidance", "覆盖路径引导"),
    ("unknown environments", "未知环境"),
    ("unknown environment", "未知环境"),
    ("bandwidth-limited environments", "带宽受限环境"),
    ("autonomous exploration", "自主探索"),
    ("autonomous aerial exploration", "自主空中探索"),
    ("autonomous uav exploration", "自主无人机探索"),
    ("aerial exploration", "空中探索"),
    ("uav exploration", "无人机探索"),
    ("drone exploration", "无人机探索"),
    ("robot navigation", "机器人导航"),
    ("trajectory planning", "轨迹规划"),
    ("path planning", "路径规划"),
    ("motion planning", "运动规划"),
    ("reinforcement learning", "强化学习"),
    ("imitation learning", "模仿学习"),
    ("neural network", "神经网络"),
    ("policy network", "策略网络"),
    ("simulation results show that", "仿真结果表明"),
    ("experimental results show that", "实验结果表明"),
    ("results show that", "结果表明"),
    ("this paper proposes", "本文提出"),
    ("this paper presents", "本文提出"),
    ("this paper studies", "本文研究"),
    ("this work proposes", "这项工作提出"),
    ("in this work", "在这项工作中"),
    ("in this paper", "在本文中"),
    ("we propose", "我们提出"),
    ("we present", "我们提出"),
    ("we introduce", "我们引入"),
    ("we develop", "我们开发了"),
    ("we design", "我们设计"),
    ("we evaluate", "我们评估"),
    ("we demonstrate", "我们验证"),
    ("we investigate", "我们研究"),
    ("our method", "我们的方法"),
    ("our approach", "我们的方法"),
    ("our framework", "我们的框架"),
    ("our system", "我们的系统"),
    ("framework", "框架"),
    ("method", "方法"),
    ("approach", "方法"),
    ("strategy", "策略"),
    ("system", "系统"),
    ("algorithm", "算法"),
    ("model", "模型"),
    ("efficient", "高效"),
    ("robust", "鲁棒"),
    ("autonomous", "自主"),
    ("exploration", "探索"),
    ("planning", "规划"),
    ("navigation", "导航"),
    ("perception", "感知"),
    ("environment", "环境"),
    ("environments", "环境"),
    ("quadrotor", "四旋翼"),
    ("drone", "无人机"),
    ("uav", "无人机"),
    ("mav", "微型飞行器"),
]


def generate_topic_tags(record: PaperRecord, keywords: list[str], limit: int = 6) -> list[str]:
    text = " ".join(
        filter(
            None,
            [
                record.title or "",
                record.abstract or "",
                " ".join(record.subjects or []),
                " ".join(record.semantic_scholar_fields_of_study or []),
            ],
        )
    ).casefold()
    tags: list[str] = []

    for keyword in record.matched_keywords or keywords:
        if keyword and keyword.casefold() in text:
            tags.append(keyword)

    for label, signals in METHOD_CATEGORIES.items():
        if any(signal in text for signal in signals):
            tags.append(label)

    tags.extend(record.semantic_scholar_fields_of_study or [])
    tags.extend(record.subjects or [])

    title_tokens = [token for token in normalize_title(record.title).split() if len(token) > 2]
    for token in title_tokens:
        if token not in STOPWORDS:
            tags.append(token)

    return unique_preserve_order(tags)[:limit]


def _contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _apply_translation_rules(text: str) -> str:
    translated = text
    for source, target in TRANSLATION_RULES:
        translated = re.sub(re.escape(source), target, translated, flags=re.IGNORECASE)
    return translated


def _normalize_translation_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ,", ",").replace(" .", ".").replace(" ;", ";").replace(" :", ":")
    text = text.replace(".", "。 ")
    text = text.replace(";", "；")
    text = text.replace(":", "：")
    text = re.sub(r"\s+([，。；：])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def translate_abstract_to_chinese(abstract: str | None) -> str | None:
    if not abstract:
        return None

    text = re.sub(r"\s+", " ", abstract).strip()
    if not text:
        return None
    if _contains_cjk(text):
        return text

    translated = _apply_translation_rules(text)
    translated = _normalize_translation_text(translated)
    return translated or text


def generate_chinese_summary(record: PaperRecord) -> str:
    translated = translate_abstract_to_chinese(record.abstract)
    if translated:
        return translated
    return "未获取到公开摘要，暂无可用的摘要中文翻译。"


def generate_overview(records: list[PaperRecord], config: SearchConfig) -> str:
    scope_label = journal_scope_label(normalize_requested_journals(config.normalized_journals()))
    if not records:
        return f"本次在 {scope_label} 范围内未得到满足条件的论文，可能是关键词过窄、时间窗口过短，或公开元数据不足。"

    keyword_counter: Counter[str] = Counter()
    topic_counter: Counter[str] = Counter()
    method_counter: Counter[str] = Counter()
    year_counter: Counter[int] = Counter()

    for record in records:
        keyword_counter.update(record.matched_keywords)
        topic_counter.update(record.topic_tags)
        method_counter.update([tag for tag in record.topic_tags if tag in METHOD_CATEGORIES])
        if record.publication_year:
            year_counter[record.publication_year] += 1

    top_keywords = "、".join(f"{kw}（{count}篇）" for kw, count in keyword_counter.most_common(4)) or "关键词分布较分散"
    top_topics = "、".join(f"{tag}（{count}篇）" for tag, count in topic_counter.most_common(5)) or "主题较分散"
    method_routes = "、".join(f"{name}（{count}篇）" for name, count in method_counter.most_common(4)) or "没有形成明显单一路线"

    overlap = keyword_overlap_counts(records)
    overlap_text = ""
    if overlap:
        pair, count = sorted(overlap.items(), key=lambda item: item[1], reverse=True)[0]
        overlap_text = f"关键词交叉最明显的是 {pair}（{count}篇），说明这些主题之间存在较强耦合。"

    recent_years = "、".join(f"{year}（{count}篇）" for year, count in year_counter.most_common(3))
    top_titles = "、".join(record.title for record in records[:3])

    parts = [
        f"本次在 {scope_label} 范围内共整理出 {len(records)} 篇机器人论文。关键词命中较集中的方向包括 {top_keywords}。",
        f"从主题标签看，论文主要分布在 {top_topics}。",
        f"从标题和摘要信号看，方法路线主要落在 {method_routes}。",
    ]
    if recent_years:
        parts.append(f"从年份分布看，结果主要集中在 {recent_years}，整体上偏向近期研究。")
    if overlap_text:
        parts.append(overlap_text)
    if top_titles:
        parts.append(f"优先建议先读前几篇排序靠前的论文，例如：{cut_text(top_titles, 120)}。")
    return "\n\n".join(parts)


def generate_keyword_observations(records: list[PaperRecord], keywords: list[str]) -> str:
    if not records:
        return "没有可用于关键词分组的论文记录。"

    lines: list[str] = []
    for keyword in keywords:
        count = sum(1 for item in records if keyword in item.matched_keywords)
        lines.append(f"- `{keyword}`：{count} 篇")

    overlap = keyword_overlap_counts(records)
    if overlap:
        top_pairs = sorted(overlap.items(), key=lambda item: item[1], reverse=True)[:5]
        lines.append("")
        lines.append("关键词交叉最多的组合：")
        for pair, count in top_pairs:
            lines.append(f"- `{pair}`：{count} 篇")

    return "\n".join(lines)
