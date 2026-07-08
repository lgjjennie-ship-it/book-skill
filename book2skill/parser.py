"""Multi-format book parser.

Supports: PDF (via pdfplumber), EPUB (via ebooklib), TXT (direct).
Returns a ParsedBook with raw text and metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ParsedBook:
    """Structured output from book parsing."""
    file_path: Path
    format: str                # "pdf" | "epub" | "txt"
    title: str = ""
    author: str = ""
    metadata: dict = field(default_factory=dict)
    pages: List[str] = field(default_factory=list)
    raw_text: str = ""         # Full concatenated text

    @property
    def page_count(self) -> int:
        return len(self.pages)

    @property
    def char_count(self) -> int:
        return len(self.raw_text)


def parse_book(file_path: str | Path) -> ParsedBook:
    """Parse a book file into structured text. Auto-detects format.

    Args:
        file_path: Path to PDF, EPUB, or TXT file.

    Returns:
        ParsedBook with raw text, pages, and metadata.

    Raises:
        ValueError: Unsupported file format.
        FileNotFoundError: File doesn't exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Book file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _parse_pdf(path)
    elif suffix == ".epub":
        return _parse_epub(path)
    elif suffix in (".txt", ".md", ".text"):
        return _parse_txt(path)
    else:
        raise ValueError(
            f"Unsupported format: {suffix}. Supported: .pdf, .epub, .txt"
        )


def _parse_pdf(path: Path) -> ParsedBook:
    """Parse PDF using pdfplumber."""
    try:
        import pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber required for PDF parsing. Install: pip install pdfplumber"
        )

    pages: List[str] = []
    metadata: dict = {}

    with pdfplumber.open(path) as pdf:
        metadata = dict(pdf.metadata or {})
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())

    raw = "\n\n".join(pages)

    # Extract title from metadata or first page
    title = metadata.get("Title", "")
    author = metadata.get("Author", "")
    if not title and pages:
        title = pages[0].split("\n")[0].strip()

    return ParsedBook(
        file_path=path,
        format="pdf",
        title=str(title or path.stem),
        author=str(author or ""),
        metadata=metadata,
        pages=pages,
        raw_text=raw,
    )


def _parse_epub(path: Path) -> ParsedBook:
    """Parse EPUB using ebooklib."""
    try:
        from ebooklib import epub, ITEM_DOCUMENT
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError(
            "ebooklib + beautifulsoup4 required. Install: pip install ebooklib beautifulsoup4"
        )

    book = epub.read_epub(str(path))
    pages: List[str] = []

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_body_content(), "html.parser")
        text = soup.get_text("\n")
        if text.strip():
            pages.append(text.strip())

    title = book.get_metadata("DC", "title")
    author = book.get_metadata("DC", "creator")
    raw = "\n\n".join(pages)

    return ParsedBook(
        file_path=path,
        format="epub",
        title=title[0][0] if title else path.stem,
        author=author[0][0] if author else "",
        metadata={
            "title": title,
            "creator": author,
        },
        pages=pages,
        raw_text=raw,
    )


def _parse_txt(path: Path) -> ParsedBook:
    """Parse plain text file with UTF-8 detection."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    # Detect title from first non-empty line
    title = ""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            title = stripped
            break

    return ParsedBook(
        file_path=path,
        format="txt",
        title=title or path.stem,
        author="",
        pages=[text],
        raw_text=text,
    )
