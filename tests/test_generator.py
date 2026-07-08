"""Tests for book2skill.generator."""

import json
import tempfile
from pathlib import Path

from book2skill.generator import generate_skills, _extract_key_points, _extract_title_keywords
from book2skill.parser import parse_book
from book2skill.toc import extract_toc, TOCEntry
from book2skill.chunker import chunk_book, Chapter


class TestGenerateSkills:
    def test_generates_complete_output(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)

        with tempfile.TemporaryDirectory() as tmp:
            result_dir = generate_skills(book, toc, chapters, tmp, "test-book")
            skill_dir = Path(tmp) / "test-book"

            # Master skill
            assert (skill_dir / "SKILL.md").exists()
            master = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            assert "name: test-book" in master
            assert "数据分析实战指南" in master

            # TOC
            assert (skill_dir / "toc.md").exists()
            toc_content = (skill_dir / "toc.md").read_text(encoding="utf-8")
            assert "目录索引" in toc_content

            # Metadata
            assert (skill_dir / "metadata.json").exists()
            meta = json.loads((skill_dir / "metadata.json").read_text(encoding="utf-8"))
            assert meta["book_slug"] == "test-book"
            assert meta["chapter_count"] == 5

            # Chapter skills
            chapters_dir = skill_dir / "chapters"
            assert chapters_dir.exists()
            ch_dirs = sorted(d for d in chapters_dir.iterdir() if d.is_dir())
            assert len(ch_dirs) == 5

            for ch_dir in ch_dirs:
                assert (ch_dir / "SKILL.md").exists()
                ch_content = (ch_dir / "SKILL.md").read_text(encoding="utf-8")
                assert "name:" in ch_content
                assert "description:" in ch_content

    def test_generated_chapter_has_navigation(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)

        with tempfile.TemporaryDirectory() as tmp:
            generate_skills(book, toc, chapters, tmp, "nav-test")
            ch_dir = sorted((Path(tmp) / "nav-test" / "chapters").iterdir())[0]
            content = (ch_dir / "SKILL.md").read_text(encoding="utf-8")
            assert "关联章节" in content or len(chapters) == 1
            if len(chapters) > 1:
                assert "下一章" in content

    def test_metadata_json_valid(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)

        with tempfile.TemporaryDirectory() as tmp:
            generate_skills(book, toc, chapters, tmp, "meta-test")
            meta_path = Path(tmp) / "meta-test" / "metadata.json"
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

            assert "chapters" in meta
            for ch_meta in meta["chapters"]:
                assert "index" in ch_meta
                assert "title" in ch_meta
                assert "slug" in ch_meta
                assert "skill_name" in ch_meta
                assert "path" in ch_meta


class TestExtractKeyPoints:
    def test_extracts_sentences(self):
        content = "数据分析是重要的。数据清洗是关键的。可视化是必要的。"
        points = _extract_key_points(content, n=3)
        assert len(points) <= 3
        assert all(isinstance(p, str) for p in points)

    def test_short_content_returns_placeholder(self):
        points = _extract_key_points("hi", n=3)
        assert len(points) >= 1
        assert isinstance(points[0], str)


class TestExtractTitleKeywords:
    def test_extracts_title_and_headings(self):
        entry = TOCEntry(
            title="第三章 数据可视化",
            level=1, page_index=0, char_offset=0,
        )
        chapter = Chapter(
            entry=entry,
            content="3.1 基本图表类型\n柱状图折线图散点图\n3.2 可视化原则\n简洁明了重点突出",
            char_count=100,
        )
        keywords = _extract_title_keywords(chapter)
        assert "数据可视化" in keywords
        assert "第三章 数据可视化" in keywords
