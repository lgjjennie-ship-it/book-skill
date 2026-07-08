# 📚 book2skill

Convert any book (PDF, EPUB, TXT) into **OpenCode-compatible AI skills**.

Drop a book in, get a structured skill directory out — master skill, chapter sub-skills, TOC index, and machine-readable metadata.

## Quick Start

```bash
# Install
pip install git+https://github.com/jennie-lai/book-skill.git

# Convert a book
book2skill mybook.pdf -o ./skills/

# Result:
# skills/mybook/
#   ├── SKILL.md           # Master skill (whole-book QA)
#   ├── toc.md             # TOC index
#   ├── metadata.json      # Machine-readable metadata
#   └── chapters/
#       ├── 01_介绍/
#       │   └── SKILL.md   # Chapter sub-skill
#       ├── 02_基础理论/
#       │   └── SKILL.md
#       └── ...
```

## Usage

```bash
# Basic: auto-detect title, output to ./skills/
book2skill mybook.pdf

# EPUB
book2skill mybook.epub -o ~/.config/opencode/skills/

# Custom slug and title
book2skill mybook.txt -s ml-handbook -t "Machine Learning Handbook"

# Preview TOC only (no generation)
book2skill mybook.pdf --toc-only

# Output metadata as JSON
book2skill mybook.pdf --json
```

### Options

| Flag | Description |
|------|-------------|
| `-o, --output` | Output directory (default: `./skills/`) |
| `-s, --slug` | Custom book slug for skill naming |
| `-t, --title` | Override auto-detected title |
| `--toc-only` | Print TOC, skip generation |
| `--json` | Output metadata.json to stdout |
| `--version` | Show version |

## Supported Formats

| Format | Extension | Parser |
|--------|-----------|--------|
| PDF | `.pdf` | pdfplumber |
| EPUB | `.epub` | ebooklib + BeautifulSoup |
| Plain Text | `.txt`, `.md` | UTF-8 direct |

## Generated Skill Structure

```
skills/{book_slug}/
├── SKILL.md              # Master skill
│   ├── Name: {book_slug}
│   ├── Triggers: book title, keywords
│   ├── Content: book summary, core concepts, chapter index
│   └── Navigation: links to all sub-skills
│
├── toc.md                # Full TOC with chapter summaries
│
├── metadata.json         # Machine-readable metadata
│   └── { title, author, chapters[], keywords[], ... }
│
└── chapters/
    ├── 01_chapter_name/
    │   └── SKILL.md      # Sub-skill
    │       ├── Name: {book_slug}-ch01
    │       ├── Triggers: chapter title, chapter number
    │       ├── Content: chapter summary, key points, compressed full text
    │       └── Related: prev/next chapter links
    └── 02_another_chapter/
        └── SKILL.md
```

## How It Works

```
Book File (PDF/EPUB/TXT)
  → [Parser]    Extract raw text + metadata
  → [TOC]       Detect chapter structure (CN/EN patterns)
  → [Chunker]   Split text into chapters
  → [Generator] Render SKILL.md files + metadata
  → Output: Structured skill directory
```

## Install as OpenCode Skills

1. Generate skills:
   ```bash
   book2skill mybook.pdf -o ~/.config/opencode/skills/
   ```

2. Restart OpenCode — skills auto-discovered from `~/.config/opencode/skills/`

3. Trigger by mentioning the book title, author, or chapter name in conversation.

## GitHub Action

Add `.github/workflows/book2skill.yml` to your book repo:

```yaml
# Place book files in books/ directory, push to trigger auto-conversion
books/
├── mybook.pdf
└── another-book.epub
```

On push, the action converts all books and uploads generated skills as an artifact.

## Development

```bash
git clone https://github.com/jennie-lai/book-skill.git
cd book-skill
pip install -e ".[dev]"

# Run tests
pytest

# Install locally
pip install .
```

## License

MIT
