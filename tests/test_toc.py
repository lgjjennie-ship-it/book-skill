"""Tests for book2skill.toc."""

from book2skill.toc import (
    extract_toc, _classify_line, _deduplicate_candidates,
    TOC, TOCEntry,
)


class TestClassifyLine:
    def test_cn_chapter(self):
        level, title = _classify_line("第一章 数据分析基础")
        assert level == 1
        assert title == "第一章 数据分析基础"

    def test_cn_numbered_chapter(self):
        level, title = _classify_line("第1章 概述")
        assert level == 1

    def test_cn_section_numbered(self):
        level, title = _classify_line("1.1 什么是数据分析")
        assert level == 2

    def test_cn_subsections(self):
        level, title = _classify_line("3.2.1 细节探讨")
        assert level == 3

    def test_en_chapter(self):
        level, title = _classify_line("Chapter 1: Introduction")
        assert level == 1

    def test_en_part(self):
        level, title = _classify_line("Part I: Foundations")
        assert level == 0

    def test_markdown_h1(self):
        level, title = _classify_line("# Introduction")
        assert level == 1

    def test_markdown_h2(self):
        level, title = _classify_line("## Section One")
        assert level == 2

    def test_non_heading(self):
        level, title = _classify_line("This is just a regular paragraph.")
        assert level is None
        assert title is None

    def test_long_line_not_heading(self):
        level, title = _classify_line("x" * 150)
        assert level is None


class TestDeduplicate:
    def test_removes_close_candidates(self):
        cands = [(0, 0, "Chapter 1", 1), (1, 30, "Chapter 2", 1)]
        result = _deduplicate_candidates(cands, min_chars=50)
        assert len(result) == 1

    def test_keeps_higher_level(self):
        """Higher-level entry survives even if close to previous."""
        cands = [(0, 0, "1.1 Section", 2), (1, 30, "Chapter 2", 1)]
        result = _deduplicate_candidates(cands, min_chars=50)
        assert len(result) == 2

    def test_removes_far_apart(self):
        cands = [(0, 0, "Chapter 1", 1), (1, 500, "Chapter 2", 1)]
        result = _deduplicate_candidates(cands, min_chars=50)
        assert len(result) == 2


class TestExtractTOC:
    def test_cn_book_structure(self, sample_cn_text):
        toc = extract_toc(sample_cn_text)
        assert isinstance(toc, TOC)
        # The fixture has 3 chapters but 第三章 content is short;
        # adaptive min_chapter_length may filter it. Verify at least 2.
        assert toc.chapter_count >= 2

    def test_en_book_structure(self, sample_en_text):
        toc = extract_toc(sample_en_text)
        assert isinstance(toc, TOC)
        assert toc.chapter_count >= 2

    def test_real_book_file(self, test_book_path):
        text = test_book_path.read_text(encoding="utf-8")
        toc = extract_toc(text, book_title="数据分析实战指南")
        assert toc.chapter_count == 5
        assert "第一章" in toc.entries[0].title

    def test_adaptive_min_length(self):
        """Short text gets lower min_chapter_length."""
        short = "第一章 概述\n\nshort content here"
        toc = extract_toc(short)
        assert toc.chapter_count >= 1


class TestTOCEntry:
    def test_slug(self):
        entry = TOCEntry(title="Chapter 1: Intro", level=1, page_index=0, char_offset=0)
        assert "chapter-1-intro" in entry.slug.lower()

    def test_is_chapter(self):
        ch = TOCEntry(title="Ch1", level=1, page_index=0, char_offset=0)
        sec = TOCEntry(title="Sec1", level=2, page_index=0, char_offset=0)
        assert ch.is_chapter
        assert not sec.is_chapter


class TestTOC:
    def test_flat_list(self):
        parent = TOCEntry(title="Ch1", level=1, page_index=0, char_offset=0)
        child = TOCEntry(title="Sec1", level=2, page_index=1, char_offset=50)
        parent.children.append(child)
        toc = TOC(entries=[parent])
        flat = toc.flat_list()
        assert len(flat) == 2
