"""Tests for book2skill.utils."""

import tempfile
from pathlib import Path

from book2skill.utils import slugify, clean_text, extract_keywords, ensure_dir


class TestSlugify:
    def test_english_text(self):
        assert slugify("Hello World") == "hello-world"

    def test_pure_cjk_falls_back_to_hash(self):
        result = slugify("第一章 数据分析基础")
        assert result.startswith("第一章数据分析基础-")
        assert len(result) <= 80

    def test_empty_string(self):
        assert slugify("") == "untitled"

    def test_ascii_with_numbers(self):
        assert slugify("Python3 Tutorial") == "python3-tutorial"

    def test_mixed_cjk_english(self):
        result = slugify("Python数据分析教程")
        assert "python" in result.lower()


class TestCleanText:
    def test_removes_tabs_and_carriage_returns(self):
        assert clean_text("hello\tworld\r\n") == "hello world"

    def test_collapses_multiple_spaces(self):
        assert clean_text("hello    world") == "hello world"

    def test_collapses_excessive_newlines(self):
        assert clean_text("line1\n\n\nline2\n\n\n\nline3") == "line1\n\nline2\n\nline3"

    def test_strips_whitespace(self):
        assert clean_text("  hello  ") == "hello"


class TestExtractKeywords:
    def test_extracts_english_keywords(self):
        text = "Python pandas numpy are essential tools for data science."
        keywords = extract_keywords(text, max_keywords=10)
        assert "python" in keywords

    def test_extracts_cn_segments(self):
        text = "数据分析基础\n数据采集\n数据可视化\nPython\npandas"
        keywords = extract_keywords(text, max_keywords=10)
        assert "数据分析基础" in keywords
        assert "python" in keywords

    def test_filters_chapter_headings(self):
        text = "第一章\n第二章\n真实关键词\nPython pandas"
        keywords = extract_keywords(text, max_keywords=10)
        assert "第一章" not in keywords
        assert "第二章" not in keywords

    def test_max_keywords_respected(self):
        text = "\n".join(f"keyword_{i}" for i in range(50))
        keywords = extract_keywords(text, max_keywords=5)
        assert len(keywords) <= 5


class TestEnsureDir:
    def test_creates_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "deep" / "nested" / "dir"
            result = ensure_dir(path)
            assert result == path
            assert result.exists()
            assert result.is_dir()
