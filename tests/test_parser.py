"""Tests for book2skill.parser."""

import pytest
from pathlib import Path

from book2skill.parser import parse_book, ParsedBook


class TestParseBook:
    def test_parse_txt(self, test_book_path):
        book = parse_book(test_book_path)
        assert isinstance(book, ParsedBook)
        assert book.format == "txt"
        assert book.title == "数据分析实战指南"
        assert book.char_count > 0
        assert "第一章" in book.raw_text
        assert "第五章" in book.raw_text

    def test_parse_txt_title_detection(self, tmp_path):
        txt = tmp_path / "test.txt"
        txt.write_text("Python Guide\n\nChapter 1\nContent here", encoding="utf-8")
        book = parse_book(txt)
        assert book.title == "Python Guide"
        assert book.format == "txt"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_book("/nonexistent/path/book.pdf")

    def test_unsupported_format(self, tmp_path):
        f = tmp_path / "book.docx"
        f.write_text("dummy")
        with pytest.raises(ValueError, match="Unsupported format"):
            parse_book(f)

    def test_parse_markdown(self, tmp_path):
        md = tmp_path / "README.md"
        md.write_text("# My Guide\n\n## Chapter 1\n\nHello world", encoding="utf-8")
        book = parse_book(md)
        assert book.format == "txt"
        assert "Hello world" in book.raw_text
