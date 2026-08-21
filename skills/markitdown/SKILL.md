---
name: markitdown
description: "用 Microsoft MarkItDown 将文件转为 Markdown。支持 PDF、DOCX、PPTX、XLSX、Images(OCR)、Audio(转录)、HTML、CSV、JSON、XML、ZIP、EPUB、YouTube URL 等 15+ 格式。当需要提取文件内容为文本/Markdown 时使用。不用于生成或编辑 docx/xlsx（那些有专门 skill）。"
---

# MarkItDown — 万物转 Markdown

Microsoft 开源工具，将各种文件格式转为 LLM 友好的 Markdown 文本。

GitHub: https://github.com/microsoft/markitdown

## 使用方式

### CLI（推荐，零安装）

```bash
# 单文件转换（uv 自动解析依赖）
uv run --with "markitdown[all]" markitdown <file>

# 输出到文件
uv run --with "markitdown[all]" markitdown document.pdf -o output.md

# 管道输入
cat document.html | uv run --with "markitdown[all]" markitdown

# 仅安装基础包（不含 OCR/音频）
uv run --with markitdown markitdown document.docx
```

### Python API

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["markitdown[all]"]
# ///
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)
```

## 格式与能力

| 格式 | 说明 | 需要额外依赖 |
|------|------|-------------|
| PDF | 全文提取 | 基础包即可 |
| DOCX | 表格、格式保留 | 基础包即可 |
| PPTX | 幻灯片+备注 | 基础包即可 |
| XLSX/CSV | 表格数据 | 基础包即可 |
| HTML | 网页清洗 | 基础包即可 |
| Images | EXIF + OCR 文字识别 | `markitdown[all]` (需 OCR 引擎) |
| Audio | 元数据 + 语音转录 | `markitdown[all]` + ffmpeg |
| JSON/XML | 结构化展示 | 基础包即可 |
| ZIP | 遍历内容 | 基础包即可 |
| EPUB | 电子书提取 | 基础包即可 |
| YouTube | 获取字幕/转录 | 基础包即可 |

## 与其他 skill 的分工

| 任务 | 用什么 |
|------|--------|
| 提取/读取文件内容 → 文本 | **markitdown**（本 skill） |
| 编辑/生成 Word 文档 | docx skill 或 python-docx |
| 编辑/生成 Excel | xlsx skill 或 openpyxl |
| 编辑/生成 PPT | pptx skill |
| PDF 复杂表格提取 | 考虑 docling 或 marker |

## 注意事项

- 对扫描版 PDF，OCR 质量取决于图像清晰度
- 音频转录需要系统安装 `ffmpeg`
- 大文件（>100MB）可能较慢，考虑先拆分
- 中文 PDF 支持良好
- `markitdown[all]` 首次运行会下载 OCR 模型（约 200MB）
