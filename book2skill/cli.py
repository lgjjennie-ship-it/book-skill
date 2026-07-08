"""CLI entry point for book2skill."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from book2skill import __version__
from book2skill.parser import parse_book
from book2skill.toc import extract_toc
from book2skill.chunker import chunk_book
from book2skill.generator import generate_skills
from book2skill.utils import slugify


def main():
    parser = argparse.ArgumentParser(
        prog="book2skill",
        description="Convert any book (PDF/EPUB/TXT) into OpenCode-compatible AI skills.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  book2skill mybook.pdf                          # Auto-detect title, output ./skills/
  book2skill mybook.epub -o ~/.config/opencode/skills/
  book2skill mybook.txt -s my-book-slug -t "My Book"
  book2skill mybook.pdf --toc-only               # Only extract TOC
  book2skill mybook.pdf --json                   # Output metadata as JSON to stdout
        """,
    )

    parser.add_argument(
        "book", type=str,
        help="Path to book file (.pdf, .epub, .txt)",
    )
    parser.add_argument(
        "-o", "--output", type=str, default="./skills",
        help="Output directory for skills (default: ./skills/)",
    )
    parser.add_argument(
        "-s", "--slug", type=str, default=None,
        help="Custom book slug for skill naming (default: auto from title)",
    )
    parser.add_argument(
        "-t", "--title", type=str, default=None,
        help="Override book title",
    )
    parser.add_argument(
        "--toc-only", action="store_true",
        help="Only extract and print table of contents",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output metadata as JSON to stdout",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"book2skill {__version__}",
    )

    args = parser.parse_args()

    book_path = Path(args.book)
    if not book_path.exists():
        print(f"Error: File not found: {book_path}", file=sys.stderr)
        sys.exit(1)

    # Parse
    print(f"📖 Parsing: {book_path.name} ...", file=sys.stderr)
    book = parse_book(book_path)

    if args.title:
        book.title = args.title

    # TOC
    print(f"📑 Extracting TOC ...", file=sys.stderr)
    toc = extract_toc(book.raw_text, book_title=book.title)

    if args.toc_only:
        for entry in toc.entries:
            indent = "  " * entry.level
            print(f"{indent}└─ {entry.title}")
        sys.exit(0)

    # Chunk
    print(f"✂️  Splitting into chapters ...", file=sys.stderr)
    chapters = chunk_book(book, toc)
    print(f"   Found {len(chapters)} chapter(s)", file=sys.stderr)

    # Generate
    print(f"🛠  Generating skills ...", file=sys.stderr)
    slug = args.slug or slugify(book.title)
    output_dir = generate_skills(book, toc, chapters, args.output, book_slug=slug)

    # Report
    print(f"\n✅ Done! Skills generated at: {output_dir}", file=sys.stderr)
    print(f"   Book: {book.title}", file=sys.stderr)
    print(f"   Chapters: {len(chapters)}", file=sys.stderr)
    print(f"   Total chars: {book.char_count:,}", file=sys.stderr)
    print(f"\n   ├── SKILL.md          (master skill)", file=sys.stderr)
    print(f"   ├── toc.md            (TOC index)", file=sys.stderr)
    print(f"   ├── metadata.json     (machine-readable)", file=sys.stderr)
    print(f"   └── chapters/         ({len(chapters)} sub-skills)", file=sys.stderr)

    if args.json:
        import json
        meta_path = output_dir / "metadata.json"
        if meta_path.exists():
            print(meta_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
