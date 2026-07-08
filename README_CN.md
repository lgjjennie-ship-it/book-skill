# 📚 book2skill — 把书变成 AI 技能

`book2skill` 是一个命令行工具，能把 PDF、EPUB、TXT 格式的电子书，自动转换成 OpenCode 能读懂的"技能文件"。转换后，你在 OpenCode 聊天框里提到书名或章节名，AI 就能像读过这本书一样回答你的问题。

---

## 目录

1. [前置准备：装好 Python](#1-前置准备装好-python)
2. [下载安装 book2skill](#2-下载安装-book2skill)
3. [转换你的第一本书](#3-转换你的第一本书)
4. [把技能部署到 OpenCode](#4-把技能部署到-opencode)
5. [在 OpenCode 中使用](#5-在-opencode-中使用)
6. [转换结果长什么样](#6-转换结果长什么样)
7. [高级用法](#7-高级用法)
8. [常见问题](#8-常见问题)

---

## 1. 前置准备：装好 Python

`book2skill` 是一个 Python 工具，所以你的电脑需要先装 Python。

### 检查是否已安装

打开终端（Mac 按 `Cmd + 空格`，搜索"终端"；Windows 搜索"命令提示符"），输入：

```bash
python3 --version
```

如果看到类似 `Python 3.10.x` 或更高版本，说明已经装好了。

如果看到 `command not found` 或 `'python3' 不是内部或外部命令`，说明还没装。

### 安装 Python（如果没装）

**Mac 用户：**
1. 打开 https://www.python.org/downloads/
2. 点击黄色按钮下载最新版 Python 安装包
3. 双击 `.pkg` 文件，一路点"继续"→"安装"即可
4. 装完后重新打开终端，输入 `python3 --version` 确认

**Windows 用户：**
1. 打开 https://www.python.org/downloads/
2. 下载 Python 安装包
3. 双击运行，**务必勾选底部的 "Add Python to PATH"**，然后点 Install
4. 装完后打开命令提示符，输入 `python --version` 确认

> 💡 安装完 Python 后，`pip`（Python 的包管理工具）会自动一同安装，下一步会用到。

---

## 2. 下载安装 book2skill

在终端中输入下面这行命令，回车：

```bash
pip3 install git+https://github.com/lgjjennie-ship-it/book-skill.git
```

你会看到类似这样的输出，说明正在下载安装：

```
Collecting git+https://github.com/lgjjennie-ship-it/book-skill.git
  Cloning https://github.com/lgjjennie-ship-it/book-skill.git to /tmp/pip-...
  Installing build dependencies ... done
  ...
Successfully installed book2skill-0.1.0 pdfplumber-0.11.4 ebooklib-0.18 ...
```

### 验证安装成功

```bash
book2skill --version
```

如果输出了版本号（如 `book2skill 0.1.0`），说明安装成功。

> **Windows 用户注意：** 如果提示 `'book2skill' 不是内部或外部命令`，关掉命令行窗口重新打开，再试一次。如果还是不行，用 `python -m book2skill --version` 代替。

---

## 3. 转换你的第一本书

### 准备工作

把你的书放在一个你知道的文件夹里。

#### 哪种格式效果最好？

> **PDF 的质量天差地别，不是每种 PDF 都能转出好效果。**

| 格式 | 推荐 | 说明 |
|------|:--:|------|
| **EPUB** `.epub` | ⭐⭐⭐ | 文字型电子书，结构清晰，首选 |
| **TXT** `.txt` | ⭐⭐⭐ | 纯文本，无格式干扰，最稳定 |
| **文字型 PDF** | ⭐⭐ | 能选中+复制文字的 PDF，如正版电子书 |
| **扫描版 PDF / 图片 PDF** | ❌ | 每页是图片，转换后全是乱码 |

**怎么快速判断？** 打开 PDF，用鼠标选中一段文字——能选中、能复制 = 文字型。选不中 = 扫描版。

**扫描版 PDF 转换后的典型症状：**
- 章节标题变乱码（如 `21 "`、`404 — 323`、`145 144.958`）
- 书名被错误识别成 `⽬录` 或空白
- 正文出现大量 `\u0000` 空字符
- 关键词全是标点符号

**扫描版 PDF 怎么办？** 先用 [Calibre](https://calibre-ebook.com/)（免费软件）转成 EPUB 或 TXT，再用 book2skill 转换。

### 执行转换

假设你的书在桌面 `mybooks` 文件夹里，叫 `机器学习实战.pdf`：

```bash
book2skill ~/Desktop/mybooks/机器学习实战.pdf
```

路径太长不想手打？在终端里先输入 `book2skill `（末尾有个空格），然后把 PDF 文件直接拖进终端窗口，路径会自动填上。

回车后，你会看到类似这样的输出：

```
📖 摘要: 机器学习实战
   章节: 15 章
   关键词: 监督学习, 无监督学习, 神经网络, ...
   → skills/机器学习实战/

✅ 已生成 16 个技能 (1 master + 15 chapters)
```

### 文件放在哪里了？

默认输出到当前目录下的 `skills/` 文件夹。比如你在桌面开的终端，文件就在 `桌面/skills/机器学习实战/`。

想换输出位置？用 `-o` 参数指定：

```bash
book2skill ~/Desktop/mybooks/机器学习实战.pdf -o ~/Documents/my-skills/
```

### 其他常用参数

```bash
# 只想看目录，不生成文件（常用：先确认目录对不对）
book2skill mybook.pdf --toc-only

# 自己指定书名
book2skill mybook.txt -t "数据分析入门"

# 自己指定英文短名（slug）
book2skill mybook.pdf -s data-analysis
```

---

## 4. 把技能部署到 OpenCode

OpenCode 会自动加载 `~/.config/opencode/skills/` 目录下的技能文件。所以只需要把生成好的技能文件夹放进去就行。

### 方法一：一键生成到 OpenCode 技能目录（推荐）

```bash
book2skill ~/Desktop/mybooks/机器学习实战.pdf -o ~/.config/opencode/skills/
```

### 方法二：生成后手动移动

```bash
# 先生成到当前目录
book2skill ~/Desktop/mybooks/机器学习实战.pdf

# 再移动到 OpenCode 技能目录
mv skills/机器学习实战 ~/.config/opencode/skills/
```

### 确认部署成功

```bash
ls ~/.config/opencode/skills/机器学习实战/
```

应该能看到：

```
SKILL.md        toc.md          metadata.json   chapters/
```

---

## 5. 在 OpenCode 中使用

1. **重启 OpenCode**（技能在启动时加载，运行中新增的需要重启）
2. 在聊天框里直接提问，AI 就会自动调用对应的书籍技能。

### 试一下

在 OpenCode 里输入：

- "帮我总结一下《机器学习实战》的主要内容"
- "《机器学习实战》第三章讲了什么？"
- "根据《机器学习实战》，决策树和随机森林有什么区别？"

AI 会自动识别你提到的书名，加载对应技能来回答，而不是靠它训练数据里可能记错的内容。

### 没生效？

检查两点：
1. 技能文件夹是不是在 `~/.config/opencode/skills/` 下？路径不对 OpenCode 找不到。
2. OpenCode 重启了吗？新增技能必须重启才能识别。

---

## 6. 转换结果长什么样

转换后，一本书会变成一个技能目录：

```
机器学习实战/                  ← 技能根目录
├── SKILL.md                  ← 主技能文件
│   （包含：书名、摘要、核心概念、全书章节目录、指向各章子技能的链接）
│
├── toc.md                    ← 完整目录索引
│   （包含：每一章的标题、摘要、关键知识点）
│
├── metadata.json             ← 机器可读的元数据
│   （json 格式，包含书名、章数、关键词列表等）
│
└── chapters/                 ← 逐章子技能
    ├── 01_机器学习基础/
    │   └── SKILL.md          ← 第 1 章技能
    │       （包含：章摘要、关键概念、上一章/下一章导航）
    │
    ├── 02_k-近邻算法/
    │   └── SKILL.md
    │
    └── ...（剩余章节）
```

**每个 SKILL.md 文件的作用：**

| 文件 | 作用 | 什么时候触发 |
|------|------|-------------|
| 根目录 `SKILL.md` | 全书总览 | 提到书名、作者、全书性问题时 |
| `chapters/01_xxx/SKILL.md` | 单章详解 | 提到具体章节名或编号时 |

---

## 7. 高级用法

### 中文书籍目录识别

`book2skill` 自动识别中文书常见的目录格式：

- `第一章 xxx` / `第1章 xxx`
- `第一节 xxx` / `第1节 xxx`
- 编号格式 `1.1`、`2.3.1` 自动建立层级关系
- 短章节（如序言）自动放宽识别阈值

### 批量转换

有多本书？一行搞定：

```bash
for book in ~/Desktop/mybooks/*.pdf; do
    book2skill "$book" -o ~/.config/opencode/skills/
done
```

### GitHub Actions 自动转换

如果你把书放在 GitHub 仓库里，可以配置每次 push 自动转换。

1. 在仓库中创建 `books/` 文件夹，放入你的 PDF/EPUB
2. 将 `.github/workflows/book2skill.yml` 复制到你的仓库
3. 每次 push 时，GitHub Actions 会自动转换并打包生成结果

```yaml
# 仓库结构示例
books/
├── 算法导论.pdf
└── 设计模式.epub
```

---

## 8. 常见问题

### Q: 提示 `command not found: book2skill`

**A:** 安装没成功或者命令没加入 PATH。试试：
```bash
python3 -m book2skill --version
```
如果能运行，之后每次用 `python3 -m book2skill` 代替 `book2skill` 即可。

如果还是报错，重新安装一次：
```bash
pip3 install --force-reinstall git+https://github.com/lgjjennie-ship-it/book-skill.git
```

### Q: 中文书名被识别成了乱码

**A:** 确保终端编码是 UTF-8。Mac/Linux 默认已是 UTF-8。Windows 用户可以在命令行里先执行：
```cmd
chcp 65001
```

### Q: PDF 转换后目录识别不准、内容有乱码

**A:** 大概率你用的是扫描版 / 图片型 PDF（每页是图片，不是文字）。症状包括章节标题变成 `21 "`、`404 — 323` 这种无意义字符串，正文出现 `\u0000` 空字符。

先用 `--toc-only` 看看识别结果：
```bash
book2skill mybook.pdf --toc-only
```
如果章节标题都很奇怪，说明文本提取本身已失败，建议：
1. 用 [Calibre](https://calibre-ebook.com/) 把 PDF 转成 EPUB 或 TXT
2. 如果能找到该书的 EPUB 版本，直接用 EPUB 转换
3. 用 `-t` 手动指定书名，至少让生成的技能文件名正确

文字型 PDF 也可能因排版复杂导致目录识别偏差，用同样方式排查。

### Q: 生成的技能文件太多，只想保留某些章节

**A:** 目前不支持筛选章节。你需要手动删除不需要的章节目录。后续版本会加入 `--chapters` 筛选参数。

### Q: 如何更新到最新版？

**A:**
```bash
pip3 install --upgrade git+https://github.com/lgjjennie-ship-it/book-skill.git
```

---

## License

MIT
