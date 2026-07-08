"""book2skill - Convert any book into OpenCode-compatible AI skills.

Pipeline:
    Book File (PDF/EPUB/TXT)
        -> [Parser] -> Raw text + metadata
        -> [TOC Extractor] -> Hierarchical table of contents
        -> [Chunker] -> Chapter segments
        -> [Skill Generator] -> SKILL.md files

Output:
    {output_dir}/{book_slug}/
    ├── SKILL.md           # Master skill — whole-book QA
    ├── toc.md             # TOC index with searchable structure
    └── chapters/
        ├── 01_chapter_name/
        │   └── SKILL.md   # Chapter-level sub-skill
        └── ...
"""

__version__ = "0.1.0"
__all__ = ["parser", "toc", "chunker", "generator", "cli"]
