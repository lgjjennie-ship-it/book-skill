"""Skill file generator - render SKILL.md from chapter data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Optional

from book2skill.chunker import Chapter, compress_content
from book2skill.parser import ParsedBook
from book2skill.toc import TOC, TOCEntry
from book2skill.utils import extract_keywords, slugify, ensure_dir


# ── Templates (inline to avoid Jinja2 dependency) ──────────────────

MASTER_SKILL_TEMPLATE = """---
name: {book_slug}
description: |
  {book_title} 全书知识库。
  触发场景：{triggers}
  关键词：{keywords}
---

# {book_title}

{meta_line}

## 本书摘要

{summary}

## 目录索引

{chapter_index}

## 使用方式

- **全书通识**：直接向我提问本书内任何概念、理论或方法。
- **章节深入**：提及具体章节名，我会加载对应子 skill 给出详细解答。
- **目录检索**：查看 [toc.md](toc.md) 快速定位章节。

## 核心概念

{key_concepts}

## 章节导航

加载以下子 skill 获取逐章详解：

{chapter_nav}
"""

CHAPTER_SKILL_TEMPLATE = """---
name: {skill_name}
description: |
  {book_title} - {chapter_title}。
  触发场景：{triggers}
  关键词：{keywords}
---

# {chapter_title}

> 出自《{book_title}》 · {chapter_label}

## 章摘要

{summary}

## 关键知识点

{key_points}

## 内容详解

{content}

{related_section}
"""

TOC_TEMPLATE = """# {book_title} - 目录索引

{meta_line}

## 全书结构

{toc_tree}

## 各章摘要

{chapter_summaries}

## 关键词索引

{keyword_index}
"""


def generate_skills(
    book: ParsedBook,
    toc: TOC,
    chapters: List[Chapter],
    output_dir: str | Path,
    book_slug: Optional[str] = None,
) -> Path:
    """Generate complete skill directory for a book.

    Args:
        book: Parsed book from parser.
        toc: Extracted TOC.
        chapters: Chapter list from chunker.
        output_dir: Parent output directory.
        book_slug: Optional custom slug. Auto-generated if None.

    Returns:
        Path to generated skill directory.
    """
    out = Path(output_dir)
    slug = book_slug or slugify(book.title or book.file_path.stem)
    book_dir = ensure_dir(out / slug)
    chapters_dir = ensure_dir(book_dir / "chapters")

    # Extract global keywords from chapter titles + English content words
    all_keywords = []
    for ch in chapters:
        clean = re.sub(r"^第[一二三四五六七八九十百千万\d]+[章節节]\s*", "", ch.title)
        all_keywords.append(clean)
        all_keywords.append(ch.title)
    # Add English keywords from content
    eng_kw = re.findall(r"\b[A-Z][a-zA-Z]{3,}(?:\s+[A-Z][a-zA-Z]{3,})?\b", book.raw_text)
    for w in eng_kw[:10]:
        if w.lower() not in {"The", "And", "For", "This", "That", "With", "From", "Chapter", "Part"}:
            all_keywords.append(w)
    # Deduplicate
    seen = set()
    all_keywords = [x for x in all_keywords if not (x in seen or seen.add(x))]

    # Generate master SKILL.md
    master_content = _render_master(book, toc, chapters, slug, all_keywords)
    (book_dir / "SKILL.md").write_text(master_content, encoding="utf-8")

    # Generate toc.md
    toc_content = _render_toc(book, toc, chapters, all_keywords)
    (book_dir / "toc.md").write_text(toc_content, encoding="utf-8")

    # Generate chapter sub-skills
    for i, chapter in enumerate(chapters):
        ch_slug = f"{i+1:02d}_{slugify(chapter.title)}"
        ch_dir = ensure_dir(chapters_dir / ch_slug)
        ch_content = _render_chapter(book, chapter, i + 1, slug, chapters)
        (ch_dir / "SKILL.md").write_text(ch_content, encoding="utf-8")

    # Generate metadata JSON (machine-readable)
    _generate_metadata(book, toc, chapters, slug, book_dir)

    return book_dir


def _render_master(
    book: ParsedBook,
    toc: TOC,
    chapters: List[Chapter],
    slug: str,
    keywords: List[str],
) -> str:
    """Render master SKILL.md."""
    title = book.title or book.file_path.stem
    meta_line = ""
    if book.author:
        meta_line = f"**作者**: {book.author}"
    if book.metadata.get("year"):
        meta_line += f" · **年份**: {book.metadata['year']}"

    # Trigger phrases
    triggers = f"《{title}》、{title}这本书、查询{title}、{slug}"
    kw_str = "、".join(keywords[:15])

    # Summary: Join first 200 chars of each chapter summary
    summaries = []
    for ch in chapters[:5]:
        if ch.content:
            summaries.append(ch.content[:150].replace("\n", " "))
    summary = "；".join(summaries) if summaries else "（无摘要）"
    if len(summary) > 500:
        summary = summary[:500] + "…"

    # Chapter index as list
    chapter_index_lines = []
    for i, ch in enumerate(chapters):
        ch_num = f"{i+1:02d}"
        chapter_index_lines.append(
            f"{ch_num}. [{ch.title}](chapters/{ch_num}_{slugify(ch.title)}/SKILL.md)"
        )
    chapter_index = "\n".join(chapter_index_lines)

    # Key concepts
    key_concepts = "\n".join(f"- {kw}" for kw in keywords[:20])

    # Chapter nav for skill loading
    chapter_nav_lines = []
    for i, ch in enumerate(chapters):
        ch_num = f"{i+1:02d}"
        skill_name = f"{slug}-ch{i+1:02d}"
        chapter_nav_lines.append(
            f"| `{skill_name}` | {ch.title} | `chapters/{ch_num}_{slugify(ch.title)}/` |"
        )
    ch_nav_header = "| Skill 名称 | 章节 | 路径 |\n|-----------|------|------|\n"
    chapter_nav = ch_nav_header + "\n".join(chapter_nav_lines)

    return MASTER_SKILL_TEMPLATE.format(
        book_slug=slug,
        book_title=title,
        meta_line=meta_line,
        triggers=triggers,
        keywords=kw_str,
        summary=summary,
        chapter_index=chapter_index,
        key_concepts=key_concepts,
        chapter_nav=chapter_nav,
    )


def _render_chapter(
    book: ParsedBook,
    chapter: Chapter,
    index: int,
    book_slug: str,
    all_chapters: List[Chapter],
) -> str:
    """Render a chapter-level SKILL.md."""
    title = book.title or book.file_path.stem
    ch_title = chapter.title
    skill_name = f"{book_slug}-ch{index:02d}"
    ch_label = f"第{index}章" if "章" not in ch_title else ch_title[:20]

    # Keywords: chapter title + section headers within content + book title
    ch_keywords = _extract_title_keywords(chapter)
    kw_str = "、".join(ch_keywords[:12])

    # Triggers
    triggers = f"{ch_title}、{title} {ch_label}、{book_slug} ch{index:02d}"

    # Summary: first 300 chars
    summary = chapter.content[:300].replace("\n", " ")
    if len(summary) == 300:
        summary += "…"

    # Key points: extract sentences that look like definitions or key claims
    key_points = _extract_key_points(chapter.content, n=8)

    # Content: compress for skill embedding
    content = compress_content(chapter.content, target_chars=8000)

    # Related chapters
    related_section = ""
    if len(all_chapters) > 1:
        related = []
        prev_idx = index - 2  # 0-based prev
        next_idx = index      # 0-based next
        if prev_idx >= 0:
            related.append(f"**上一章**: {all_chapters[prev_idx].title}")
        if next_idx < len(all_chapters):
            related.append(f"**下一章**: {all_chapters[next_idx].title}")
        if related:
            related_section = "\n## 关联章节\n\n" + "\n".join(related)

    return CHAPTER_SKILL_TEMPLATE.format(
        skill_name=skill_name,
        book_title=title,
        chapter_title=ch_title,
        chapter_label=ch_label,
        triggers=triggers,
        keywords=kw_str,
        summary=summary,
        key_points="\n".join(f"- {p}" for p in key_points),
        content=content,
        related_section=related_section,
    )


def _render_toc(
    book: ParsedBook,
    toc: TOC,
    chapters: List[Chapter],
    keywords: List[str],
) -> str:
    """Render toc.md."""
    title = book.title or book.file_path.stem
    meta_line = ""
    if book.author:
        meta_line = f"作者: {book.author}"

    # TOC tree
    toc_lines = []
    for entry in toc.entries:
        prefix = "  " * entry.level
        toc_lines.append(f"{prefix}- {entry.title}")
        for child in entry.children:
            toc_lines.append(f"{prefix}  - {child.title}")

    toc_tree = "\n".join(toc_lines) if toc_lines else "（自动提取的章节列表见主 SKILL.md）"

    # Chapter summaries
    ch_summaries = []
    for i, ch in enumerate(chapters):
        summary = ch.content[:120].replace("\n", " ")
        ch_summaries.append(f"### {i+1}. {ch.title}\n\n{summary}...")
    chapter_summaries = "\n\n".join(ch_summaries) if ch_summaries else "（无）"

    # Keyword index
    kw_index = "\n".join(f"- {kw}" for kw in keywords[:30])

    return TOC_TEMPLATE.format(
        book_title=title,
        meta_line=meta_line,
        toc_tree=toc_tree,
        chapter_summaries=chapter_summaries,
        keyword_index=kw_index,
    )


def _extract_key_points(content: str, n: int = 8) -> List[str]:
    """Extract n key points/sentences from content."""
    import re
    # Split by sentence boundaries for both CN and EN
    sentences = re.split(
        r"(?<=[。！？.!?])\s*|(?<=\n)",
        content[:3000],
    )
    sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    if not sentences:
        return ["（内容解析中）"]

    # Prioritize sentences with definition/indicator phrases
    indicators = [
        "定义", "是指", "关键", "核心", "重要", "必须", "注意",
        "define", "key", "important", "critical",
        "is", "are", "means",
    ]
    scored = []
    for s in sentences:
        score = sum(1 for ind in indicators if ind.lower() in s.lower())
        scored.append((score, s))

    scored.sort(key=lambda x: -x[0])
    selected = [s for _, s in scored[:n]]
    if len(selected) < n:
        selected.extend(sentences[len(selected):n - len(selected)])
    return selected[:n]


def _extract_title_keywords(chapter: Chapter) -> List[str]:
    """Extract keywords from chapter title and section headings.

    Uses title/heading structure rather than content n-grams for
    reliable Chinese keyword extraction without a segmenter.
    """
    import re

    keywords = []
    title = chapter.entry.title
    content = chapter.content[:3000]

    # Chapter title itself (stripped of numbering)
    clean_title = re.sub(r"^第[一二三四五六七八九十百千万\d]+[章節节]\s*", "", title)
    if clean_title:
        keywords.append(clean_title)

    # Add the full title
    keywords.append(title)

    # Extract section headings from content (numbered or markdown)
    for pattern in [
        r"\d+\.\d+\s+(.{2,40})",       # "1.1 Title"
        r"\d+\.\s+(.{2,40})",           # "1. Title"  
        r"^#{1,3}\s+(.{2,40})",         # "## Title"
    ]:
        for m in re.finditer(pattern, content, re.MULTILINE):
            kw = m.group(1).strip()
            if kw and len(kw) >= 2 and kw not in keywords:
                keywords.append(kw)

    # English words from content (filtered)
    eng_words = re.findall(r"\b[A-Z][a-zA-Z]{2,}(?:\s+[A-Z][a-zA-Z]{2,})?\b", content)
    for w in eng_words[:3]:
        if w.lower() not in {"The", "And", "For", "This", "That", "With", "From"}:
            if w not in keywords:
                keywords.append(w)

    return keywords[:12]


def _generate_metadata(
    book: ParsedBook,
    toc: TOC,
    chapters: List[Chapter],
    slug: str,
    book_dir: Path,
) -> None:
    """Write machine-readable metadata.json."""
    meta = {
        "book_slug": slug,
        "title": book.title,
        "author": book.author,
        "format": book.format,
        "total_chars": book.char_count,
        "chapter_count": len(chapters),
        "chapters": [
            {
                "index": i + 1,
                "title": ch.title,
                "slug": ch.slug,
                "char_count": ch.char_count,
                "level": ch.level,
                "keywords": ch.keywords[:10],
                "skill_name": f"{slug}-ch{i+1:02d}",
                "path": f"chapters/{i+1:02d}_{slugify(ch.title)}/SKILL.md",
            }
            for i, ch in enumerate(chapters)
        ],
    }
    (book_dir / "metadata.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
