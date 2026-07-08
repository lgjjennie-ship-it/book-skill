"""Chapter chunker - split book content by TOC entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from book2skill.parser import ParsedBook
from book2skill.toc import TOC, TOCEntry


@dataclass
class Chapter:
    """A single chapter/section with its full content."""
    entry: TOCEntry
    content: str           # Full text of this chapter
    char_count: int = 0
    keywords: List[str] = field(default_factory=list)

    @property
    def title(self) -> str:
        return self.entry.title

    @property
    def slug(self) -> str:
        return self.entry.slug

    @property
    def level(self) -> int:
        return self.entry.level


def chunk_book(book: ParsedBook, toc: TOC) -> List[Chapter]:
    """Split parsed book into chapters based on TOC.

    Args:
        book: ParsedBook from parser.
        toc: TOC from toc extraction.

    Returns:
        List of Chapter objects with full content.
    """
    text = book.raw_text
    top_entries = toc.entries  # Only top-level chapters, not subsections
    chapters: List[Chapter] = []

    for i, entry in enumerate(top_entries):
        start = entry.char_offset
        end = top_entries[i + 1].char_offset if i + 1 < len(top_entries) else len(text)
        content = text[start:end].strip()

        if len(content) < 50:
            continue  # Skip empty/tiny chapters

        from book2skill.utils import extract_keywords
        keywords = extract_keywords(content, max_keywords=15)

        chapters.append(Chapter(
            entry=entry,
            content=content,
            char_count=len(content),
            keywords=keywords,
        ))

    return chapters


def compress_content(content: str, target_chars: int = 8000) -> str:
    """Intelligently compress long chapter content for skill embedding.

    Strategy:
    1. Keep first 15% (intro/summary usually at start)
    2. Keep last 10% (conclusion)
    3. Evenly sample the middle 75%
    4. Never cut mid-sentence on CJK or English

    Args:
        content: Full chapter text.
        target_chars: Approximate target length.

    Returns:
        Compressed content string.
    """
    if len(content) <= target_chars:
        return content

    # Split into paragraphs
    paragraphs = content.split("\n")
    # Filter empty/short
    paragraphs = [p for p in paragraphs if len(p.strip()) > 20]

    if len(paragraphs) <= 5:
        return content[:target_chars]

    # Allocate: 20% head, 60% middle, 20% tail
    total_paras = len(paragraphs)
    head_count = max(2, total_paras // 5)
    tail_count = max(2, total_paras // 5)
    middle_count = max(2, total_paras - head_count - tail_count)

    # Evenly sample middle
    middle_start = head_count
    middle_end = total_paras - tail_count
    step = max(1, (middle_end - middle_start) // middle_count)

    selected = paragraphs[:head_count]
    for i in range(middle_start, middle_end, step):
        if i < middle_end:
            selected.append(paragraphs[i])
    selected.extend(paragraphs[-tail_count:])

    result = "\n\n".join(selected)

    # Truncate if still too long
    if len(result) > target_chars:
        result = result[:target_chars]
        # Try to cut at sentence boundary
        for cut_char in ["。", ".", "！", "!", "？", "?", "\n"]:
            last = result.rfind(cut_char, target_chars - 500)
            if last > target_chars // 2:
                result = result[: last + 1]
                break

    return result
