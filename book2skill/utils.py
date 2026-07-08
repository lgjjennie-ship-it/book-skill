"""Shared utilities for book2skill."""

import hashlib
import re
import unicodedata
from pathlib import Path
from typing import List, Optional


def slugify(text: str) -> str:
    """Convert arbitrary text to a filesystem-safe slug.

    For CJK-heavy text, extracts ASCII words + appends a short hash to
    ensure uniqueness while remaining human-readable.
    """
    if not text:
        return "untitled"

    # Extract ASCII words
    ascii_words = re.findall(r"[a-zA-Z0-9]+", text)
    if ascii_words:
        base = "-".join(w.lower() for w in ascii_words)
        if len(base) >= 4:
            return base[:80]

    # Pure CJK: use a short hash
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    # Try to extract a meaningful prefix from the text
    prefix = text.strip()[:20]
    prefix = re.sub(r"[^\w\u4e00-\u9fff]", "", prefix)
    if prefix:
        return f"{prefix}-{h}"[:80]

    return f"ch{h}"


def clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, strip junk."""
    text = re.sub(r"[\t\r]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_metadata_from_text(text: str, lines: int = 50) -> dict:
    """Heuristic metadata extraction from book opening lines."""
    head = text.split("\n")[:lines]
    joined = "\n".join(head)

    meta: dict = {"title": "", "author": "", "isbn": "", "publisher": "", "year": ""}

    isbn_match = re.search(r"ISBN[:\s]*([\d-]{10,17})", joined, re.IGNORECASE)
    if isbn_match:
        meta["isbn"] = isbn_match.group(1).strip("- ")

    year_match = re.search(
        r"(?:©|Copyright|Published)\s*(?:in\s*)?(19|20)\d{2}",
        joined, re.IGNORECASE,
    )
    if year_match:
        meta["year"] = year_match.group(0)[-4:]

    if head:
        meta["title"] = head[0].strip()

    return meta


def extract_keywords(text: str, max_keywords: int = 20) -> List[str]:
    """Extract topic-significant keywords from text.

    Splits on punctuation/whitespace for CJK, uses word boundaries for English.
    """
    from collections import Counter

    # Chinese: extract from heading-like segments (short, standalone lines)
    # rather than from running text (unreliable without jieba/cutword)
    cn_segments = []
    for line in text.split("\n"):
        line = line.strip()
        if 2 <= len(line) <= 60:
            cn_segments.append(line)

    # English words >= 3 chars
    eng = re.findall(r"\b[a-zA-Z]{3,}\b", text)

    counter = Counter(cn_segments + [w.lower() for w in eng])

    stops_cn = {
        "可以", "一个", "这个", "我们", "他们", "不是", "没有", "什么",
        "因为", "所以", "但是", "如果", "虽然", "而且", "或者", "关于",
        "进行", "使用", "通过", "根据", "包括", "主要", "问题", "方法",
        "其中", "所有", "知识", "大家", "理解", "不同", "一样", "很多",
        "第一章", "第二章", "第三章", "第四章", "第五章",
        "第六章", "第七章", "第八章", "第九章", "第十章",
        "第一", "第二", "第三", "第四", "第五",
    }
    stops_en = {
        "this", "that", "with", "from", "have", "what", "when",
        "they", "them", "about", "their", "which", "would", "there",
        "these", "those", "could", "should", "other", "chapter",
        "the", "and", "are", "was", "for", "not", "but", "all",
        "can", "has", "had", "its", "been", "more", "will",
    }

    keywords = [
        w for w, _ in counter.most_common(max_keywords * 3)
        if w not in stops_cn and w not in stops_en and len(w) >= 2
    ]
    return keywords[:max_keywords]


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, return path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
