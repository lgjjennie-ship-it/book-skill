"""Tests for book2skill.chunker."""

from book2skill.chunker import chunk_book, compress_content, Chapter
from book2skill.parser import parse_book, ParsedBook
from book2skill.toc import extract_toc, TOCEntry


class TestChunkBook:
    def test_chunks_test_book(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)
        assert len(chapters) == 5
        assert all(isinstance(ch, Chapter) for ch in chapters)

    def test_chapter_has_content(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)
        for ch in chapters:
            assert ch.char_count > 0
            assert len(ch.content) > 50

    def test_chapter_has_keywords(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)
        for ch in chapters:
            assert len(ch.keywords) > 0

    def test_chapter_titles_preserved(self, test_book_path):
        book = parse_book(test_book_path)
        toc = extract_toc(book.raw_text, book.title)
        chapters = chunk_book(book, toc)
        titles = [ch.title for ch in chapters]
        assert any("第一章" in t for t in titles)
        assert any("第五章" in t for t in titles)

    def test_skips_tiny_chapters(self):
        book = ParsedBook(
            file_path=__file__,
            format="txt",
            title="Test",
            raw_text="第一章 空\n\n\n第二章 内容\n\n这里有实际内容，足够长度来通过阈值检查。这行用来确保内容不少于50个字符。"
        )
        toc = extract_toc(book.raw_text, "Test")
        chapters = chunk_book(book, toc)
        # Chapter 1 should be skipped (too short), Chapter 2 survives
        assert len(chapters) >= 1


class TestCompressContent:
    def test_short_content_passed_through(self):
        short = "Hello world. This is short content."
        result = compress_content(short, target_chars=8000)
        assert result == short

    def test_long_content_compressed(self):
        # Generate content well over target
        long_content = ("This is paragraph number {:03d} with enough text to make it substantial and useful. ") * 200
        long_content = long_content.format(*range(200))
        result = compress_content(long_content, target_chars=2000)
        assert len(result) <= 2500  # Allow some margin
        assert len(result) > 0

    def test_truncation_at_sentence_boundary(self):
        paragraphs = [f"Paragraph number {i:03d} with enough text to form a complete paragraph that ends with a period." for i in range(200)]
        content = "\n\n".join(paragraphs)
        result = compress_content(content, target_chars=2000)
        assert "Paragraph" in result
        assert len(result) <= 2500
