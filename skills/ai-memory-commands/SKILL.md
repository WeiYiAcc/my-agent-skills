---
name: ai-memory-commands
description: >
  ai-memory 长期记忆的快捷交互命令。涵盖 /recall（搜索记忆）、/remember（写入记忆）、/forget（删除记忆）、/recap（项目概览）、/memory（最近页面）。当用户说「记住这个」、「搜索记忆」、「回忆一下」、「删除那条笔记」、「项目概况」、「最近改了什么」，或使用 /recall /remember /forget /recap /memory 命令时触发。也在用户提到 ai-memory、wiki 页面、handoff、长期记忆时触发。
---

# ai-memory 快捷命令

为 ai-memory MCP server 提供用户友好的交互层。ai-memory 是一个基于 Rust + SQLite FTS5 的长期记忆系统，通过 MCP 暴露 16 个工具。这些命令将最常用的 5 个操作封装为简洁的工作流。

## 命令总览

| 命令 | 用途 | 对应 MCP tool |
|------|------|--------------|
| `/recall <query>` | 搜索过去的记忆 | `ai_memory_memory_query` |
| `/remember <content>` | 写入持久记忆 | `ai_memory_memory_write_page` |
| `/forget <path-or-query>` | 删除指定记忆 | `ai_memory_memory_delete_page` |
| `/recap` | 项目活动概览 | `ai_memory_memory_explore` |
| `/memory [N]` | 最近更新的页面 | `ai_memory_memory_recent` |

---

## /recall — 搜索记忆

当用户想找回过去的决策、知识、经验时使用。

### 工作流

1. 用用户的文本作为 `query` 调用 `ai_memory_memory_query`，`limit: 10`
2. 按相关度排序展示结果（path、标题、snippet）
3. 高分结果优先展示
4. 如果零结果，建议 2-3 个替代搜索词，不要编造

### 示例

用户说："我们之前是怎么决定用 SQLite 的？"

```
调用: ai_memory_memory_query { "query": "SQLite 选型 决策" }
展示: decisions/db-choice.md — "选择 SQLite 因为零外部依赖..."
```

### 反模式

- ❌ 搜索无结果时凭记忆编造："我们可能讨论过..."
- ✅ "没找到匹配的记忆。试试 `数据库`、`持久化`、`存储选型`？"

### 同时搜索 ariadne-fact

如果用户的问题可能同时存在于 ai-memory 和 ariadne-fact 中，两边都搜：
- `ai_memory_memory_query` — 项目记忆
- `ariadne_fact_search_facts` — 全局知识库

汇总两边的结果呈现给用户。

---

## /remember — 写入记忆

当用户想永久保存一条知识、决策、规则、经验教训时使用。

### 工作流

1. 从用户的话中提取核心内容
2. 判断合适的 path 和 tier：
   - `decisions/<slug>.md` — 架构/技术决策（tier: semantic, pinned: true）
   - `concepts/<slug>.md` — 持久知识/事实（tier: semantic）
   - `gotchas/<slug>.md` — 踩坑记录（tier: semantic）
   - `_rules/<slug>.md` — 项目规则（tier: procedural, pinned: true）
   - `notes/<slug>.md` — 一般笔记（tier: episodic）
3. body 第一行用 `# 标题`（ai-memory 自动从 H1 提取标题）
4. 调用 `ai_memory_memory_write_page`
5. 确认写入成功，告知 path 和 tags

### 判断是否同时写 ariadne-fact

如果内容是**通用的、跨项目可复用的知识**（工具选型、技术决策、操作手册），同时写入 ariadne-fact：
- 调用 `ariadne_fact_upsert_fact`

如果内容是**项目特定的**（某次会话的上下文、某个 bug 的排查过程），只写 ai-memory。

### 示例

用户说："记住 docx skill 是 Anthropic 官方的，不是微软的"

```
path: "concepts/docx-skill-origin.md"
body: "# Docx Skill 来源\n\ndocx skill 是 Anthropic 官方提供的..."
tier: "semantic"
tags: ["docx", "tooling"]
pinned: true
```

### 反模式

- ❌ path 用中文或空格：`notes/我的笔记.md`
- ✅ path 用 kebab-case：`notes/my-note.md`
- ❌ 忘记在 body 开头写 `# 标题`
- ✅ 始终以 `# ` 开头，让 ai-memory 自动提取 title

---

## /forget — 删除记忆

当用户想删除错误或过时的记忆时使用。这是破坏性操作。

### 工作流

1. 如果用户给了精确 path → 直接用
2. 如果用户给了模糊描述 → 先用 `ai_memory_memory_query` 搜索匹配项
3. **展示将被删除的页面，要求明确确认**
4. 确认后调用 `ai_memory_memory_delete_page`
5. 报告删除结果

### 反模式

- ❌ 搜到匹配就直接删除，不等用户确认
- ✅ 列出匹配项，问"要删除这些吗？"，等明确 yes

---

## /recap — 项目概览

当用户想了解"最近在做什么"、"项目现在是什么状态"时使用。

### 工作流

1. 调用 `ai_memory_memory_explore`（无参数，或带 `focus`）
2. 展示 LLM 生成的项目摘要
3. 如果 LLM 未配置，fallback 到 `ai_memory_memory_briefing` 展示结构化数据

### 示例

用户说："recap" 或 "这个项目最近在干嘛"

```
调用: ai_memory_memory_explore {}
返回: 项目活动摘要，根据距上次活动的时间自动调整详细程度
```

---

## /memory — 最近页面

快速查看 wiki 最近更新了什么。

### 工作流

1. 解析参数：数字 = limit，默认 10
2. 调用 `ai_memory_memory_recent { "limit": N }`
3. 列表展示：path、标题、更新时间

### 示例

用户说："/memory 5"

```
调用: ai_memory_memory_recent { "limit": 5 }
展示:
  1. decisions/docx-skill-vs-python-docx.md — 更新于 2 小时前
  2. skills/markitdown-setup.md — 更新于 3 小时前
  ...
```

---

## 通用规则

- 所有命令的结果只展示工具实际返回的数据，不编造
- 空结果是合法答案，不要试图填充
- path 始终用 kebab-case 英文
- body 始终以 `# Title` 开头
- 不要传 `title` 参数（issue #67 的已知 bug）
- 默认 `project` 和 `workspace` 留空（ai-memory 自动解析当前项目）
