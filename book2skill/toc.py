"""Table of Contents extraction.

Uses line-by-line scanning to detect chapter/section structure
from raw book text, supporting both Chinese and English books.
Avoids re.MULTILINE + ^ to work around Python 3.13 re CJK bug.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass
class TOCEntry:
    """A single entry in the table of contents."""
    title: str
    level: int           # 0 = part, 1 = chapter, 2 = section, 3 = subsection
    page_index: int      # Line index in the text
    char_offset: int     # Character offset in raw text
    children: List[TOCEntry] = field(default_factory=list)
    content_summary: str = ""  # First 200 chars of content

    @property
    def slug(self) -> str:
        from book2skill.utils import slugify
        return slugify(self.title)

    @property
    def is_chapter(self) -> bool:
        return self.level <= 1


@dataclass
class TOC:
    """Full table of contents."""
    entries: List[TOCEntry] = field(default_factory=list)
    book_title: str = ""

    @property
    def chapter_count(self) -> int:
        return len(self.entries)

    def flat_list(self) -> List[TOCEntry]:
        result = []
        for entry in self.entries:
            result.append(entry)
            result.extend(self._flatten_children(entry))
        return result

    def _flatten_children(self, entry: TOCEntry) -> List[TOCEntry]:
        result = []
        for child in entry.children:
            result.append(child)
            result.extend(self._flatten_children(child))
        return result


# ── Line-level patterns (no ^, no MULTILINE) ─────────────────────

_CN_CHAPTER_RE = re.compile(
    r"第?\s*([一二三四五六七八九十百千万零\d]+)\s*[章節节](?:\s*[：:]\s*)?\s*(.*)",
)
_CN_PART_RE = re.compile(
    r"第?\s*([一二三四五六七八九十百千万零\d]+)\s*[部篇编](?:\s*[：:]\s*)?\s*(.*)",
)
_CN_SECTION_RE = re.compile(
    r"([一二三四五六七八九十百千万零\d]+(?:\.[一二三四五六七八九十百千万零\d]+)*)\s*[节](?:\s*[：:]\s*)?\s*(.*)",
)
_EN_CHAPTER_RE = re.compile(
    r"(?:Chapter|CHAPTER|Ch\.?)\s*(\d+|[IVXLCDMivxlcdm]+)\s*[.:\s-]+\s*(.+)",
)
_EN_PART_RE = re.compile(
    r"(?:Part|PART)\s*(\d+|[IVXLCDMivxlcdm]+)\s*[.:\s-]+\s*(.+)",
)
# Numbered heading: "1.1 Title" or "1. Title"
_NUM_HEADING_RE = re.compile(
    r"(\d+(?:\.\d+)*)\s+(.+)",
)
# Markdown: ## Title
_MD_HEADING_RE = re.compile(
    r"(#{1,4})\s+(.+)",
)


def extract_toc(
    raw_text: str,
    book_title: str = "",
    min_chapter_length: int = 200,
) -> TOC:
    """Extract table of contents from raw book text.

    Scans line-by-line for chapter/section patterns, avoiding
    re.MULTILINE compatibility issues with CJK text in Python 3.13.

    Args:
        raw_text: Full book text.
        book_title: Optional book title.
        min_chapter_length: Minimum chars between entries for validity.

    Returns:
        Structured TOC with entries and hierarchy.
    """
    # Auto-scale minimum chapter length to total text
    if min_chapter_length <= 0:
        min_chapter_length = 200
    min_chapter_length = min(200, max(30, len(raw_text) // 8))
    lines = raw_text.split("\n")

    # Collect candidates: (line_index, char_offset, title, level)
    candidates: List[Tuple[int, int, str, int]] = []

    char_pos = 0
    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            char_pos += len(line) + 1
            continue

        # Determine level and title from line patterns
        level, title = _classify_line(stripped)
        if level is not None and title:
            # Use the stripped line as title for cleaner output
            candidates.append((line_idx, char_pos, stripped[:100], level))

        char_pos += len(line) + 1

    if not candidates:
        return _fallback_toc(raw_text, book_title)

    # Deduplicate: remove candidates too close together (keep first)
    candidates = _deduplicate_candidates(candidates, min_chars=50)

    # Build hierarchy
    entries = _build_hierarchy_from_candidates(candidates, raw_text, min_chapter_length)

    return TOC(entries=entries, book_title=book_title)


def _classify_line(line: str) -> Tuple[Optional[int], Optional[str]]:
    """Classify a line as chapter/section heading.

    Returns (level, title) or (None, None) if not a heading.
    Levels: 0=part, 1=chapter, 2=section, 3=subsection
    """
    line = line.strip()
    if len(line) > 120:
        return None, None  # Too long to be a heading

    # Try Chinese chapter: 第一章 / 第1章
    m = _CN_CHAPTER_RE.fullmatch(line)
    if m:
        return 1, line

    # Try Chinese part: 第一篇
    m = _CN_PART_RE.fullmatch(line)
    if m:
        return 0, line

    # Try Chinese section: 第X节 / X.Y 节
    m = _CN_SECTION_RE.fullmatch(line)
    if m:
        depth = m.group(1).count(".") + 1
        return min(depth + 1, 3), line

    # Try English chapter
    m = _EN_CHAPTER_RE.fullmatch(line)
    if m:
        return 1, line

    # Try English part
    m = _EN_PART_RE.fullmatch(line)
    if m:
        return 0, line

    # Try numbered heading
    m = _NUM_HEADING_RE.fullmatch(line)
    if m:
        depth = m.group(1).count(".")
        return min(depth + 1, 3), line

    # Try markdown heading
    m = _MD_HEADING_RE.fullmatch(line)
    if m:
        level = min(len(m.group(1)), 3)
        return level, line

    return None, None


def _deduplicate_candidates(
    candidates: List[Tuple[int, int, str, int]],
    min_chars: int = 50,
) -> List[Tuple[int, int, str, int]]:
    """Remove candidates that are too close together.

    Never dedup a higher-level (lower number) entry — a chapter heading
    should survive even if close to a subsection heading.
    """
    if not candidates:
        return []
    result = [candidates[0]]
    for cand in candidates[1:]:
        prev_level = result[-1][3]
        curr_level = cand[3]
        # Keep if far enough apart OR if current is higher-level (more important)
        if cand[1] - result[-1][1] >= min_chars or curr_level < prev_level:
            result.append(cand)
    return result


def _build_hierarchy_from_candidates(
    candidates: List[Tuple[int, int, str, int]],
    text: str,
    min_length: int,
) -> List[TOCEntry]:
    """Build hierarchical TOC from candidate list.

    For each candidate, the content range extends to the next candidate
    at the SAME OR HIGHER level (not to a child subsection).
    """
    entries: List[TOCEntry] = []

    for i, (line_idx, char_offset, title, level) in enumerate(candidates):
        # Find next candidate at same-or-higher level (skip children)
        next_offset = len(text)
        for j in range(i + 1, len(candidates)):
            next_level = candidates[j][3]
            if next_level <= level:
                next_offset = candidates[j][1]
                break

        content = text[char_offset:next_offset].strip()

        # Only skip if content is too short AND this is not a top-level chapter
        if len(content) < min_length and level > 0 and i > 0:
            continue

        summary = content[:300].replace("\n", " ")

        entry = TOCEntry(
            title=title,
            level=level,
            page_index=line_idx,
            char_offset=char_offset,
            content_summary=summary,
        )

        _insert_hierarchical(entries, entry)

    return entries


def _insert_hierarchical(
    entries: List[TOCEntry],
    new_entry: TOCEntry,
) -> None:
    """Insert entry into hierarchical TOC based on level."""
    parent = None
    for entry in reversed(entries):
        if entry.level < new_entry.level:
            parent = entry
            break
        found = _find_parent_in_children(entry.children, new_entry)
        if found:
            parent = found
            break

    if parent:
        parent.children.append(new_entry)
    else:
        entries.append(new_entry)


def _find_parent_in_children(
    children: List[TOCEntry],
    new_entry: TOCEntry,
) -> Optional[TOCEntry]:
    for child in reversed(children):
        if child.level < new_entry.level:
            return child
        found = _find_parent_in_children(child.children, new_entry)
        if found:
            return found
    return None


def _fallback_toc(text: str, book_title: str) -> TOC:
    """Generate TOC when no patterns match — split by blank lines."""
    chunks = re.split(r"\n{2,}", text)
    entries = []
    for i, chunk in enumerate(chunks[:50]):
        chunk = chunk.strip()
        if len(chunk) < 100:
            continue
        title_line = chunk.split("\n")[0]
        entry = TOCEntry(
            title=title_line[:80],
            level=1,
            page_index=i,
            char_offset=text.find(chunk),
            content_summary=chunk[:200],
        )
        entries.append(entry)

    return TOC(entries=entries, book_title=book_title)
