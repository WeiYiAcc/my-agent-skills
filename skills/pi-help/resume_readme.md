# Session 恢复 (Resume) — 完整手册

Pi Agent 会话恢复与管理的一站式文档。从 2 分钟速查到架构深潜，按需阅读。

---

## 📑 目录

- **[Part 1: ⚡ 快速参考](#part-1--快速参考)** — 2 分钟上手
  - [3 个最常用命令](#3-个最常用命令)
  - [命令速查表](#命令速查表)
  - [选择器快捷键速查](#选择器快捷键速查)
  - [常见场景工作流](#常见场景工作流)
- **[Part 2: 📖 使用指南](#part-2--使用指南)** — 10 分钟学会
  - [4 种恢复方式](#4-种恢复方式)
  - [会话范围与排序](#会话范围与排序)
  - [搜索与过滤](#搜索与过滤)
  - [会话命名](#会话命名)
  - [会话删除](#会话删除)
  - [会话持久化](#会话持久化)
  - [高级用法](#高级用法)
- **[Part 3: 🔧 技术详解](#part-3--技术详解)** — 开发者深潜
  - [核心功能清单](#核心功能清单)
  - [工作目录编码](#工作目录编码)
  - [会话信息收集](#会话信息收集)
  - [选择器 UI 架构](#选择器-ui-架构)
  - [排序模式实现](#排序模式实现)
  - [会话恢复流程](#会话恢复流程)
  - [会话命名机制](#会话命名机制)
  - [会话删除机制](#会话删除机制)
  - [--continue 快速恢复](#--continue-快速恢复)
  - [性能优化](#性能优化)
  - [错误处理](#错误处理)
  - [扩展集成](#扩展集成)
  - [设计决策](#设计决策)
- **[Part 4: 🔍 问题诊断](#part-4--问题诊断)** — 排错手册
  - [发现的问题](#发现的问题)
  - [解决方案总结](#解决方案总结)
  - [故障排除 FAQ](#故障排除-faq)

---

# Part 1: ⚡ 快速参考

> 2 分钟速查。记住这些就够日常使用了。

## 3 个最常用命令

### 1️⃣ 交互式选择会话（推荐）

```bash
/resume
```

打开会话选择器，选择要恢复的会话。

### 2️⃣ 快速恢复最近会话

```bash
pi -c          # 或 pi --continue
```

直接恢复最近的会话，无需选择。

### 3️⃣ 给会话命名

```bash
/name 我的项目 - 功能 A
```

给当前会话起个有意义的名字，便于后续查找。

## 命令速查表

| 命令 | 说明 | 场景 |
|------|------|------|
| `/resume` | 打开会话选择器 | 在 Pi 中输入 |
| `/name <name>` | 给当前会话命名 | `/name 项目名称` |
| `/export` | 导出会话为 HTML | 归档分享 |
| `pi -c` | 恢复最近会话 | 命令行快速恢复 |
| `pi -r` | 启动时选择会话 | 命令行选择恢复 |
| `pi --session <path>` | 指定会话文件 | 恢复特定会话 |

## 选择器快捷键速查

### 导航与操作

| 快捷键 | 功能 |
|--------|------|
| ⬆️ / ⬇️ | 上下选择 |
| Page Up / Page Down | 快速滚动 |
| Home / End | 跳到开始/结束 |
| Enter | 恢复选中会话 |
| Esc | 取消 |

### 排序、过滤、管理

| 快捷键 | 功能 |
|--------|------|
| **Tab** | 切换范围（Current Folder ↔ All） |
| **Ctrl+S** | 切换排序（Threaded → Recent → Fuzzy） |
| **Ctrl+N** | 切换名称过滤（All ↔ Named） |
| **Ctrl+P** | 显示/隐藏完整路径 |
| **Ctrl+R** | 重命名选中会话 |
| **Ctrl+D** | 删除选中会话 |

### 搜索

| 方法 | 效果 |
|------|------|
| 直接输入 | 模糊搜索 |
| `re:正则` | 正则搜索 |
| `"精确词"` | 精确匹配 |
| Backspace | 删除搜索字符 |

## 常见场景工作流

### 多项目切换

```bash
cd ~/project1 && pi -c     # 恢复 project1 的会话
cd ~/project2 && pi -c     # 恢复 project2 的会话（自动分离）
```

### 找某个之前的会话

```bash
/resume                     # 打开选择器
bugfix                      # 输入关键词搜索
Enter                       # 恢复
```

### 保存重要会话

```bash
/name 项目最终版本 - 部署前   # 命名后下次 /resume 容易找
```

### 整理旧会话

```bash
/resume → Ctrl+S（Recent 排序）→ 选择旧会话 → Ctrl+D → Enter 确认
```

### 会话作为检查点

```bash
/name checkpoint-1          # 标记检查点
# 做实验...
/name checkpoint-2          # 标记另一个
# 后来用 /resume 搜 checkpoint-1 恢复
```

### 跨目录查看

```bash
/resume → Tab（切换到 All）→ 搜索其他项目的会话
```

---

# Part 2: 📖 使用指南

> 10 分钟学会所有功能。

## 4 种恢复方式

### 方式 1：交互式恢复（推荐）

在 Pi 中输入 `/resume`，UI 显示会话列表：

```
Resume Session (Current Folder)
◉ Current Folder | ○ All
[会话列表...]
```

用 ⬆️/⬇️ 选择，Enter 恢复，Tab 切换范围，Esc 取消。

### 方式 2：快速恢复最近会话

```bash
pi -c                  # 或 pi --continue
```

直接加载最近一次的会话，无需选择。

### 方式 3：启动时选择会话

```bash
pi -r                  # 或 pi --resume
```

启动 Pi 时打开会话选择器。

### 方式 4：指定具体会话

```bash
pi --session ~/.pi/agent/sessions/--mnt-c-Users-user--/2026-02-19T12-52-38-830Z_<uuid>.jsonl
```

## 会话范围与排序

### 范围 (Scope)

会话按工作目录组织，存储在 `~/.pi/agent/sessions/` 下：

```
~/.pi/agent/sessions/
├── --mnt-c-Users-user--/          ← /mnt/c/Users/user 的会话
├── --home-user--/                 ← /home/user 的会话
└── --home-user-.config-other--/   ← /home/user/.config/other 的会话
```

| 范围 | 说明 | 切换 |
|------|------|------|
| **Current Folder** | 只显示当前 cwd 的会话（默认） | Tab |
| **All** | 显示所有目录的会话 | Tab |

### 排序模式

按 **Ctrl+S** 切换：

| 模式 | 说明 |
|------|------|
| **Threaded** | 树形结构，显示分支关系（默认） |
| **Recent** | 按修改时间，最新在上 |
| **Fuzzy** | 模糊搜索模式，按匹配度排序 |

## 搜索与过滤

### 搜索

在选择器中直接输入即可搜索：

- **模糊搜索**：输入关键词（如 `bug fix feature`）
- **正则搜索**：`re:bug.*fix`
- **精确搜索**：`"exact phrase"`

### 名称过滤

按 **Ctrl+N** 切换：

| 模式 | 说明 |
|------|------|
| **All** | 显示所有会话（默认） |
| **Named** | 只显示已命名的会话 |

## 会话命名

默认会话只有时间戳+UUID，难以区分。命名的好处：

- ✅ 快速识别会话内容
- ✅ 在 `/resume` 中搜索和过滤
- ✅ 分享时更清晰

**方法 1**：在当前会话中 → `/name 我的项目 - 修复登录 bug`

**方法 2**：在 `/resume` 选择器中 → 选中会话 → Ctrl+R → 输入名字 → Enter

## 会话删除

**方法 1**：`/resume` 中选中 → Ctrl+D → Enter 确认（移入回收站，可恢复）

**方法 2**：手动删除文件

```bash
ls ~/.pi/agent/sessions/--mnt-c-Users-user--/
rm ~/.pi/agent/sessions/--mnt-c-Users-user--/2026-02-19T12-52-38-830Z_*.jsonl
```

> ⚠️ 手动 `rm` 删除通常无法恢复。建议先 `/name` 重要会话，再小心删除。

## 会话持久化

### 自动保存

Pi 自动将对话保存到会话文件中：每条消息、工具调用结果、扩展状态均自动写入。

### 恢复时发生什么

```
恢复会话 → 加载所有历史消息 → 恢复扩展状态 → 重建工作环境 → 继续对话
```

### 存储位置

```
~/.pi/agent/sessions/
└── --<编码的工作目录>--/
    ├── 2026-02-19T12-52-38-830Z_<uuid>.jsonl
    ├── 2026-02-19T13-00-45-120Z_<uuid>.jsonl
    └── ...
```

编码方式：`/path/to/dir` → `--path-to-dir--`

## 高级用法

### 会话分支

Pi 支持会话分支（branching）。修改会话历史时自动创建分支，原始会话保持不变，可以同时探索多个方向。

### 会话导出

```bash
/export <session_id>    # 导出为 HTML

# 或直接复制会话文件
cp ~/.pi/agent/sessions/.../file.jsonl ~/shared/
```

---

# Part 3: 🔧 技术详解

> 开发者深潜。源码级别的实现分析。

## 核心功能清单

| 功能 | 说明 | 状态 |
|------|------|------|
| 会话列表扫描 | 扫描当前 cwd 的所有会话 | ✅ |
| 会话跨目录扫描 | 列出所有 cwd 的会话 | ✅ |
| 会话排序 | Threaded / Recent / Fuzzy | ✅ |
| 会话搜索 | 模糊 / 正则 / 精确 | ✅ |
| 会话过滤 | 按名称过滤（All / Named） | ✅ |
| 会话选择器 UI | 交互式选择界面 | ✅ |
| 会话恢复 | 加载并切换会话 | ✅ |
| 会话命名 | 人类可读的名称 | ✅ |
| 会话删除 | 回收站 / 直接删除 | ✅ |
| 会话重命名 | 选择器中快速重命名 | ✅ |

## 工作目录编码

会话按 cwd 分离存储。编码规则：

```
cwd: /mnt/c/Users/weiyiacc
↓ 移除前导斜杠 → mnt/c/Users/weiyiacc
↓ 用 - 替换 / 和 : → mnt-c-Users-weiyiacc
↓ 两端加 -- → --mnt-c-Users-weiyiacc--
```

```javascript
function getDefaultSessionDir(cwd) {
  const safePath = `--${cwd.replace(/^[/\\]/, "").replace(/[/\\:]/g, "-")}--`
  return join(homedir(), ".pi", "agent", "sessions", safePath)
}
```

| cwd | 编码后目录名 |
|-----|------------|
| `/mnt/c/Users/weiyiacc` | `--mnt-c-Users-weiyiacc--` |
| `/home/weiyiacc` | `--home-weiyiacc--` |
| `/home/weiyiacc/.config/roles` | `--home-weiyiacc-.config-roles--` |

## 会话信息收集

每个会话被表示为 `SessionInfo` 对象：

```typescript
interface SessionInfo {
  path: string              // 文件完整路径
  id: string                // Session UUID
  cwd: string               // 工作目录
  name?: string             // 会话名称（可选）
  created: Date             // 创建时间
  modified: Date            // 最后修改时间
  messageCount: number      // 消息数
  firstMessage: string      // 第一条消息预览
  allMessagesText: string   // 所有消息文本（用于搜索）
  parentSessionPath?: string // 父会话路径（分支）
}
```

**加载逻辑：**

```typescript
// 当前目录会话
static async list(cwd, sessionDir, onProgress) {
  const dir = sessionDir ?? getDefaultSessionDir(cwd)
  const sessions = await listSessionsFromDir(dir, onProgress)
  sessions.sort((a, b) => b.modified.getTime() - a.modified.getTime())
  return sessions
}

// 所有目录会话（并行加载）
static async listAll(onProgress) {
  const sessionsDir = getSessionsDir()  // ~/.pi/agent/sessions/
  const dirs = (await readdir(sessionsDir)).filter(e => e.isDirectory())
  const results = await Promise.all(
    dirs.map(dir => listSessionsFromDir(join(sessionsDir, dir), onProgress))
  )
  return results.flat().sort((a, b) => b.modified.getTime() - a.modified.getTime())
}
```

**单个会话解析：**

```typescript
async function buildSessionInfo(filePath) {
  const entries = parseJSONL(await readFile(filePath, "utf8"))
  const header = entries[0]
  if (header.type !== "session") return null

  let name, messageCount = 0, firstMessage = ""
  for (const entry of entries) {
    if (entry.type === "session_info" && entry.name) name = entry.name.trim()
    if (entry.type === "message") {
      messageCount++
      if (!firstMessage && entry.message.role === "user")
        firstMessage = extractTextContent(entry.message)
    }
  }

  return { path: filePath, id: header.id, cwd: header.cwd, name,
    created: new Date(header.timestamp),
    modified: getSessionModifiedDate(entries, header, statSync(filePath).mtime),
    messageCount, firstMessage: firstMessage || "(no messages)" }
}
```

## 选择器 UI 架构

```
SessionSelectorComponent (主容器)
├── SessionSelectorHeader (标题栏)
│   ├── Scope 指示 (Current / All)
│   ├── Sort 模式 (Threaded / Recent / Fuzzy)
│   ├── Name 过滤 (All / Named)
│   └── Progress / Status 消息
└── SessionList (会话列表)
    ├── SearchInput (搜索框)
    └── [会话项...]
```

**初始化流程：**

```
showSessionSelector()
  → new SessionSelectorComponent(currentSessionsLoader, allSessionsLoader, onSelect)
  → loadCurrentSessions()
  → loadScope("current", "initial")
  → await currentSessionsLoader()
```

- UI 在加载时显示进度条
- 切换 scope 时取消前一个加载并启动新的

## 排序模式实现

### Threaded（树形结构）

```typescript
function buildSessionTree(sessions) {
  const parents = sessions.filter(s => !s.parentSessionPath)
  const children = sessions.filter(s => s.parentSessionPath)
  return parents.map(parent => ({
    session: parent,
    children: children.filter(c => c.parentSessionPath === parent.path)
  }))
}
```

### Recent（按时间）

```typescript
sessions.sort((a, b) => b.modified.getTime() - a.modified.getTime())
```

### Fuzzy（模糊搜索）

```typescript
function filterAndSortSessions(sessions, query) {
  const scored = sessions.map(s => ({
    session: s, score: calculateFuzzyScore(query, s.name || s.firstMessage)
  }))
  return scored.filter(i => i.score > threshold)
    .sort((a, b) => b.score - a.score).map(i => i.session)
}
```

### 搜索语法解析

```typescript
function filterSessions(query) {
  const trimmed = query.trim()
  if (trimmed.startsWith("re:"))
    return sessions.filter(s => new RegExp(trimmed.slice(3)).test(s.name || s.firstMessage))
  if (trimmed.startsWith('"') && trimmed.endsWith('"'))
    return sessions.filter(s => (s.name || s.firstMessage).includes(trimmed.slice(1, -1)))
  return fuzzyFilter(sessions, trimmed)  // 默认模糊搜索
}
```

## 会话恢复流程

```
用户选择 → onSelect(sessionPath) → handleResumeSession()
```

```typescript
async function handleResumeSession(sessionPath) {
  // 1. 停止加载动画、清理 UI 状态
  pendingMessagesContainer.clear()
  pendingTools.clear()

  // 2. 切换会话
  await session.switchSession(sessionPath)
  // → closeCurrentSession() → SessionManager.open(path) → initializeSession() → emit("session_start")

  // 3. 渲染历史消息
  chatContainer.clear()
  for (const entry of session.getEntries()) {
    if (entry.type === "message") chatContainer.addChild(renderMessage(entry.message))
    else if (entry.type === "custom") emitEvent("custom_entry", entry)
  }
  chatContainer.scroll("end")
  showStatus("Resumed session")
}
```

## 会话命名机制

会话名称存储为会话文件中的特殊条目（非单独文件）：

```json
{ "type": "session_info", "id": "...", "timestamp": "...", "name": "我的项目" }
```

```typescript
// /name 命令
if (text.startsWith("/name ")) {
  sessionManager.appendSessionInfo(text.slice(6).trim())
}

// /resume 中 Ctrl+R 重命名
async confirmRename(value) {
  await renameSession(sessionPath, value.trim())
  sessionManager.appendSessionInfo(value.trim())
}
```

## 会话删除机制

```typescript
async deleteSessionFile(sessionPath) {
  try {
    await execSync("trash " + sessionPath)   // 优先回收站
    return { ok: true, method: "trash" }
  } catch {
    try {
      await unlink(sessionPath)               // 回退直接删除
      return { ok: true, method: "unlink" }
    } catch (err) { return { ok: false, error: err.message } }
  }
}

// 删除后从列表中移除并更新 UI
currentSessions = currentSessions.filter(s => s.path !== sessionPath)
allSessions = allSessions.filter(s => s.path !== sessionPath)
```

## --continue 快速恢复

```typescript
static continueRecent(cwd, sessionDir) {
  const dir = sessionDir ?? getDefaultSessionDir(cwd)
  const mostRecent = findMostRecentSession(dir)
  return mostRecent
    ? new SessionManager(cwd, dir, mostRecent, true)
    : new SessionManager(cwd, dir, undefined, true)  // 无会话则新建
}

function findMostRecentSession(sessionDir) {
  return readdirSync(sessionDir)
    .filter(f => f.endsWith(".jsonl"))
    .map(f => ({ path: join(sessionDir, f), mtime: statSync(join(sessionDir, f)).mtime }))
    .sort((a, b) => b.mtime.getTime() - a.mtime.getTime())[0]?.path || null
}
```

## 性能优化

| 策略 | 实现 |
|------|------|
| **并行加载** | `Promise.all(dirs.map(dir => listSessionsFromDir(...)))` |
| **延迟初始化** | "All" 会话在按 Tab 时才加载 |
| **缓存** | 切换 scope 时重用已加载的结果 |
| **进度反馈** | 加载时实时更新进度条 |
| **竞态控制** | 序列号防止过时结果覆盖新结果 |

```typescript
// 竞态控制示例
allLoadSeq = 0
async loadScope(scope) {
  const seq = ++this.allLoadSeq
  const sessions = await loader()
  if (seq !== this.allLoadSeq) return  // 已过时，丢弃
  sessionList.setSessions(sessions, ...)
}
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 会话文件读取失败 | `try/catch` → 返回 `null`，跳过无效文件 |
| 会话目录不存在 | `mkdirSync(dir, { recursive: true })` 自动创建 |
| 并发修改 | 序列号检查，丢弃过时结果 |

## 扩展集成

```typescript
// 恢复会话时触发 session_start 事件
emitEvent("session_start", { sessionPath, previousSession: oldSessionPath })

// 扩展监听并恢复状态（如 Persona）
extension.on("session_start", (event, ctx) => {
  for (const entry of ctx.sessionManager.getEntries()) {
    if (entry.type === "custom" && entry.customType === "my_type") { /* 恢复 */ }
  }
})

// 扩展存储自定义状态
pi.appendEntry("custom_type", { data: value })
```

## 设计决策

| 决策 | 原因 |
|------|------|
| 按工作目录分组 | 自然分离项目，避免混乱，符合用户直觉 |
| Threaded 作为默认排序 | 显示分支关系，理解会话历史逻辑流 |
| 名称存储在会话文件中 | 名称跟随文件（分享时包含），避免单独索引 |
| 优先 trash 而非直接删除 | 误操作可恢复，不可用时自动回退 |

---

# Part 4: 🔍 问题诊断

> 用户报告 `/resume` "总是无法找到上一次的 session"。以下是完整的排错分析。

## 发现的问题

### 1. 多工作目录会话分离

会话按 cwd 分离存储。在不同目录启动 Pi 时，会话互不可见。

```
--mnt-c-Users-weiyiacc--/  (50 个会话)    ← /mnt/c/Users/weiyiacc
--home-weiyiacc--/         (28 个会话)    ← /home/weiyiacc
--home-weiyiacc-.config-aichat-roles--/ (1 个会话)
```

✅ **按 Tab 切换到 "All" 范围**

### 2. Threaded 排序不直观

默认 Threaded 排序在 50 个会话嵌套后难以浏览。

✅ **按 Ctrl+S 切换到 "Recent" 排序**

### 3. 会话识别困难

大多数会话无名字，只有时间戳和 UUID。

✅ **用 `/name` 命名 + Ctrl+N 过滤已命名会话**

## 解决方案总结

| 问题 | 解决方式 | 快捷键 |
|------|---------|--------|
| 找不到其他目录的会话 | 切换到 "All" 范围 | **Tab** |
| 列表太多找不到 | 切换到 "Recent" 排序 | **Ctrl+S** |
| 无法区分会话 | 给会话命名 | `/name` |
| 只看重要会话 | 过滤已命名会话 | **Ctrl+N** |
| 搜索特定会话 | 直接输入关键词 | 直接打字 |
| 快速恢复上次 | 命令行启动时 | `pi -c` |

## 故障排除 FAQ

### `/resume` 没有找到任何会话？

**检查清单：**

1. 确认工作目录：`pwd`
2. 在 `/resume` 中按 **Tab** → 切换到 "All"
3. 检查文件：`ls ~/.pi/agent/sessions/`

### 无法恢复上次的会话？

```bash
pi -c                    # 方法 1：自动恢复最近会话
ls -lt ~/.pi/agent/sessions/--mnt-c-Users-user--/ | head -5   # 方法 2：手动检查
```

### 会话太多找不到想要的？

```bash
/name 重要的会话          # 给重要会话命名
/resume → Ctrl+N         # 只显示已命名的
```

### 误删会话能恢复吗？

- ✅ `/resume` 中 Ctrl+D 删除 → 在回收站，通常可恢复
- ❌ 手动 `rm` 删除 → 通常无法恢复

### 会话保存在哪里？

```
~/.pi/agent/sessions/--<编码的工作目录>--/
# 例: /mnt/c/Users/weiyiacc → ~/.pi/agent/sessions/--mnt-c-Users-weiyiacc--/
```

---

## 相关文档

| 方向 | 文档 | 关系 |
|------|------|------|
| ⬆ 上级 | [SKILL.md](./SKILL.md) | Pi-help 快速参考（同目录） |
| ↔ 参考 | Pi 官方 session 文档: `~/.npm-global/lib/node_modules/@mariozechner/pi-coding-agent/docs/session.md` |

---

*一站式 Session 恢复手册。按需查阅，从速查到深潜。*
