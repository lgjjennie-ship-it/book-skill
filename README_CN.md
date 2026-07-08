# 📚 book2skill

将任意书籍（PDF / EPUB / TXT）转换为 **OpenCode 兼容的 AI 技能**。

扔一本书进去，输出一个结构化的技能目录——主技能、逐章子技能、目录索引、机器可读的元数据。

## 快速开始

```bash
# 安装
pip install git+https://github.com/lgjjennie-ship-it/book-skill.git

# 转换一本书
book2skill mybook.pdf -o ./skills/

# 输出结构：
# skills/mybook/
#   ├── SKILL.md           # 主技能（全书问答）
#   ├── toc.md             # 目录索引
#   ├── metadata.json      # 机器可读元数据
#   └── chapters/
#       ├── 01_介绍/
#       │   └── SKILL.md   # 章节子技能
#       ├── 02_基础理论/
#       │   └── SKILL.md
#       └── ...
```

## 使用方式

```bash
# 基础用法：自动识别书名，输出到 ./skills/
book2skill mybook.pdf

# EPUB 格式
book2skill mybook.epub -o ~/.config/opencode/skills/

# 自定义 slug 和书名
book2skill mybook.txt -s ml-handbook -t "机器学习实战"

# 仅预览目录，不生成技能
book2skill mybook.pdf --toc-only

# 输出元数据 JSON
book2skill mybook.pdf --json
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `-o, --output` | 输出目录（默认 `./skills/`） |
| `-s, --slug` | 自定义书籍 slug，用于技能命名 |
| `-t, --title` | 覆盖自动识别的书名 |
| `--toc-only` | 仅提取并打印目录，不生成技能文件 |
| `--json` | 输出 metadata.json 到标准输出 |
| `--version` | 显示版本号 |

## 支持格式

| 格式 | 扩展名 | 解析器 |
|--------|-----------|--------|
| PDF | `.pdf` | pdfplumber |
| EPUB | `.epub` | ebooklib + BeautifulSoup |
| 纯文本 | `.txt`, `.md` | UTF-8 直接读取 |

## 生成技能结构

```
skills/{book_slug}/
├── SKILL.md              # 主技能
│   ├── 名称：{book_slug}
│   ├── 触发词：书名、关键词
│   ├── 内容：全书摘要、核心概念、章节目录
│   └── 导航：指向所有子技能的链接
│
├── toc.md                # 完整目录 + 各章摘要
│
├── metadata.json         # 机器可读元数据
│   └── { title, author, chapters[], keywords[], ... }
│
└── chapters/
    ├── 01_章节名/
    │   └── SKILL.md      # 子技能
    │       ├── 名称：{book_slug}-ch01
    │       ├── 触发词：章节名、编号
    │       ├── 内容：章摘要、关键知识点、压缩全文
    │       └── 关联：上一章/下一章 导航链接
    └── 02_另一章节/
        └── SKILL.md
```

## 工作流程

```
书籍文件（PDF/EPUB/TXT）
  → [Parser]    提取原始文本 + 元数据
  → [TOC]       识别章节目录结构（中文/英文模式）
  → [Chunker]   按章节切分文本
  → [Generator] 渲染 SKILL.md 文件 + 元数据
  → 输出：结构化技能目录
```

## 中文书籍支持

`book2skill` 原生支持中文书籍的目录提取：

- **中文章节识别**：`第一章`、`第1章`、`第X节` 等模式
- **子节层级**：`1.1`、`3.2.1` 编号格式自动建层级树
- **自适应阈值**：短文本（如测试样章）自动降低最小章节长度要求
- **纯中文 slug**：`第一章 数据分析基础` → `第一章数据分析基础-16788f53`（MD5 后缀确保唯一）
- **标题关键词**：从章节标题和子标题提取关键词，避免无分词器下的 n-gram 噪声

## 安装为 OpenCode 技能

1. 生成技能文件：
   ```bash
   book2skill mybook.pdf -o ~/.config/opencode/skills/
   ```

2. 重启 OpenCode —— 技能从 `~/.config/opencode/skills/` 自动发现

3. 在对话中提及书名、章节名即可触发对应技能

## GitHub Actions

将 `.github/workflows/book2skill.yml` 添加到你的书籍仓库：

```yaml
# 将书籍文件放入 books/ 目录，push 时自动转换
books/
├── mybook.pdf
└── another-book.epub
```

每次 push 时，Action 会转换所有书籍并将生成的技能文件打包上传为 artifact。

## 开发

```bash
git clone https://github.com/lgjjennie-ship-it/book-skill.git
cd book-skill
pip install -e ".[dev]"

# 运行测试
pytest

# 本地安装
pip install .
```

## License

MIT
