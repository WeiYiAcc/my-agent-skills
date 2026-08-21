---
name: logseq-mcp
description: "Logseq MCP server 使用规范。通过 mcp() 工具操作 Logseq graph。列表项必须拆分为独立 block。"
---

# Logseq MCP 写入规范

通过 `mcp({ tool: "upsertNodes", ... })` 操作 Logseq graph 时，必须遵守以下规则。

## Block 粒度规则（最重要）

**每个列表项、每个段落、每个 heading 必须是独立的 block。**

Logseq 的数据模型：一个 block = 一个原子内容单元。不要把多行内容塞进一个 block title。

### ❌ 错误写法

```json
{"operation": "add", "entityType": "block", "data": {
  "page-id": "temp-page",
  "title": "- item one\n- item two\n- item three"
}}
```

### ✅ 正确写法

```json
{"operation": "add", "entityType": "block", "data": {"page-id": "temp-page", "title": "item one"}},
{"operation": "add", "entityType": "block", "data": {"page-id": "temp-page", "title": "item two"}},
{"operation": "add", "entityType": "block", "data": {"page-id": "temp-page", "title": "item three"}}
```

## 可用 Tools

通过 `mcp({ tool: "...", server: "logseq", args: '...' })` 调用：

| Tool | 用途 |
|------|------|
| `getPage` | 读取页面内容（含 blocks） |
| `listPages` | 列出所有页面 |
| `listTags` | 列出所有标签（支持 expand 查继承） |
| `listProperties` | 列出所有属性 |
| `upsertNodes` | **创建/编辑** page, block, tag, property |

## upsertNodes 用法

```json
mcp({ tool: "upsertNodes", server: "logseq", args: '{"operations": [...], "dry-run": true}' })
```

### 创建 page + blocks

```json
{"operations": [
  {"operation": "add", "entityType": "page", "id": "temp-id", "data": {"title": "Page Title"}},
  {"operation": "add", "entityType": "block", "data": {"page-id": "temp-id", "title": "First block"}},
  {"operation": "add", "entityType": "block", "data": {"page-id": "temp-id", "title": "Second block"}}
]}
```

### 给 page 加 tag

tags 参数必须是 **uuid 字符串**，先用 `listTags` 查到 uuid：

```json
{"operation": "add", "entityType": "page", "id": "temp-id", "data": {
  "title": "My Page",
  "tags": ["<tag-uuid>"]
}}
```

### tag 继承（层级关系）

```json
{"operation": "add", "entityType": "tag", "data": {
  "title": "SubTag",
  "class-extends": ["ParentTag"]
}}
```

### dry-run

测试不写入：`"dry-run": true`

## 注意事项

- block title 不要包含 `- ` 前缀（Logseq 自动渲染为列表）
- block title 不要包含 `## ` 前缀（用 block property heading 代替）
- 一个 upsertNodes 调用里的 operations 按顺序执行
- `id` 字段：page 用临时字符串（如 `"temp-xxx"`），后续 block 用 `page-id` 引用

## graphthulhu-logseq 工具使用规范

实际操作走 `graphthulhu-logseq` server（非 `logseq` server），工具名前缀为 `graphthulhu_logseq_*`。

### 写入层级结构（重要）

**写入日记或任何有层级的内容前，必须先规划完整的 block 树结构，用一次 `graphthulhu_logseq_upsert_blocks` 的 `children` 嵌套一次性写完。**

❌ 禁止：分批 `append_blocks` 后再用 `move_block` 调整层级——`move_block` 在复杂层级下行为不稳定，容易把 block 插入到错误的父节点。

✅ 正确做法：

```json
{
  "page": "Jun 17th, 2026",
  "blocks": [
    {
      "content": "顶级标题",
      "children": [
        {"content": "二级节点"},
        {
          "content": "另一个二级节点",
          "children": [
            {"content": "三级子项 A"},
            {"content": "三级子项 B"}
          ]
        }
      ]
    }
  ]
}
```

### 层级约定（用户偏好）

- **顶级 block** — 主题标题，无缩进
- **二级 block（children）** — 各节（排除方案/可用方案等），作为主题的子节点
- **三级 block** — 各条目，作为节的子节点
- **四级 block** — 条目的补充说明

### 常用工具

| 工具 | 用途 |
|------|------|
| `graphthulhu_logseq_get_page` | 读取页面（`name`, `compact: true`, `depth`） |
| `graphthulhu_logseq_upsert_blocks` | 批量创建带层级的 blocks（支持 `children`） |
| `graphthulhu_logseq_append_blocks` | 追加平铺 blocks（无层级时用） |
| `graphthulhu_logseq_update_block` | 更新单个 block 内容（`uuid`, `content`） |
| `graphthulhu_logseq_delete_block` | 删除 block（`uuid`） |
| `graphthulhu_logseq_move_block` | 移动 block（层级复杂时慎用） |
