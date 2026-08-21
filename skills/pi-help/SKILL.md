---
name: pi-help
description: "Pi 编码代理的使用方法、命令、快捷键、配置参考手册。涵盖 pi-cli、pi-mono 项目结构、Skills 系统、Session 管理、扩展开发等。当用户询问如何使用 Pi 工具、配置 Pi、开发 Pi Skills、或查询 pi-mono 相关信息时使用。"
---
# Pi Help — Pi CLI 快速参考手册

当用户询问 Pi CLI 的使用方法、命令、快捷键、配置等问题时，使用此 skill。

## 使用方式

**优先使用下方的「快速参考」内置缓存直接回答用户**，不够时再按底部「查询策略」逐级查找。

### 本地文档索引

Pi 安装目录下有完整文档，docs 目录包含以下专题：

| 文件 | 内容 |
|------|------|
| `session.md` | Session 文件格式、管理 |
| `settings.md` | 所有配置项 |
| `keybindings.md` | 键绑定配置 |
| `extensions.md` | 扩展开发 |
| `skills.md` | Skill 开发 |
| `prompt-templates.md` | 提示模板 |
| `themes.md` | 主题定制 |
| `models.md` | 模型配置 |
| `providers.md` | Provider 配置 |
| `packages.md` | Pi Packages 共享 |
| `compaction.md` | 上下文压缩机制 |
| `tree.md` | Session Tree 导航 |
| `tui.md` | TUI 组件 |
| `sdk.md` | SDK 嵌入使用 |
| `rpc.md` | RPC 模式 |
| `json.md` | JSON 输出模式 |
| `shell-aliases.md` | Shell 别名配置 |
| `terminal-setup.md` | 终端设置 |
| `windows.md` | Windows 平台注意事项 |
| `termux.md` | Android Termux 使用 |
| `custom-provider.md` | 自定义 Provider |
| `development.md` | 开发贡献指南 |

## 快速参考（内置缓存）

### 交互模式命令（输入 `/` 触发）

| 命令 | 说明 |
|------|------|
| `/login`, `/logout` | OAuth 认证登录/登出 |
| `/model` | 切换模型（也可用 Ctrl+L） |
| `/scoped-models` | 启用/禁用 Ctrl+P 循环的模型 |
| `/settings` | 设置（thinking level、主题、消息投递、传输方式） |
| `/resume` | 选择并恢复历史 session |
| `/new` | 开始新 session |
| `/name <name>` | 给当前 session 命名 |
| `/session` | 显示 session 信息（路径、token、花费） |
| `/tree` | 跳转到 session 树中任意节点继续 |
| `/fork` | 从当前分支创建新 session |
| `/compact [prompt]` | 手动压缩上下文，可附自定义指令 |
| `/copy` | 复制最后一条助手消息到剪贴板 |
| `/export [file]` | 导出 session 为 HTML |
| `/share` | 上传为私有 GitHub Gist 并生成分享链接 |
| `/reload` | 重新加载扩展、skill、提示模板、上下文文件 |
| `/hotkeys` | 显示所有快捷键 |
| `/changelog` | 显示版本历史 |
| `/quit`, `/exit` | 退出 |
| `/skill:name` | 触发已加载的 skill |
| `/templatename` | 展开提示模板 |

### 常用快捷键

| 按键 | 功能 |
|------|------|
| `Ctrl+C` | 清空编辑器 |
| `Ctrl+C` ×2 | 退出 |
| `Escape` | 取消/中止 |
| `Escape` ×2 | 打开 `/tree` |
| `Ctrl+L` | 打开模型选择器 |
| `Ctrl+P` / `Shift+Ctrl+P` | 向前/向后循环模型 |
| `Shift+Tab` | 循环 thinking level |
| `Ctrl+O` | 折叠/展开工具输出 |
| `Ctrl+T` | 折叠/展开 thinking 块 |
| `Ctrl+V` | 粘贴图片 |
| `Shift+Enter` | 多行输入（Windows Terminal 用 Ctrl+Enter） |

### 编辑器功能

| 功能 | 方式 |
|------|------|
| 文件引用 | 输入 `@` 模糊搜索项目文件 |
| 路径补全 | Tab 补全路径 |
| 执行命令 | `!command` 运行并发送输出给 LLM |
| 静默命令 | `!!command` 运行但不发送输出 |

### 消息队列（agent 工作时）

| 按键 | 功能 |
|------|------|
| `Enter` | 队列一条**引导消息**（中断当前工具后投递） |
| `Alt+Enter` | 队列一条**跟进消息**（agent 完成后投递） |
| `Escape` | 中止并恢复队列消息到编辑器 |
| `Alt+Up` | 取回队列消息到编辑器 |

### Session 管理

```bash
pi -c                  # 继续最近的 session
pi -r                  # 浏览并选择历史 session
pi --no-session        # 临时模式（不保存）
pi --session <path>    # 使用指定 session 文件
```

Session 保存在 `~/.pi/agent/sessions/`，按工作目录组织。

### 配置文件位置

| 位置 | 范围 |
|------|------|
| `~/.pi/agent/settings.json` | 全局配置 |
| `.pi/settings.json` | 项目配置（覆盖全局） |
| `~/.pi/agent/AGENTS.md` | 全局上下文指令 |
| `AGENTS.md` / `CLAUDE.md` | 项目上下文指令 |
| `.pi/SYSTEM.md` | 替换默认系统提示 |
| `APPEND_SYSTEM.md` | 追加系统提示 |
| `~/.pi/agent/keybindings.json` | 键绑定自定义 |

### CLI 常用参数

```bash
pi                                    # 交互模式
pi "prompt"                           # 带初始提示的交互模式
pi -p "prompt"                        # 非交互模式（处理后退出）
pi --model sonnet                     # 指定模型
pi --model openai/gpt-4o             # 跨 provider 指定模型
pi --model sonnet:high               # 模型 + thinking level
pi --thinking high                    # 设置 thinking level
pi --tools read,bash                  # 限制工具
pi @file.md "analyze this"           # 引用文件
pi --export session.jsonl output.html # 导出 session 为 HTML
```

## 深度参考文档

| 文档 | 路径 | 说明 |
|------|------|------|
| Session 恢复手册 | [resume_readme.md](./resume_readme.md)（同目录） | `/resume` 完整用法、快捷键、排序模式、源码分析、故障排除 |

---

## 查询策略（按优先级）

当以上内置缓存不够时，按以下顺序逐级查找：

### ⭐ 特别提醒：Skill 相关问题

**如果用户问关于 Skill、skills.md、或如何开发/加载 Skill 的问题**，直接 `read` 以下文件：

```bash
read ~/.npm-global/lib/node_modules/pi-amplike/node_modules/@mariozechner/pi-coding-agent/docs/skills.md
```

这个文件包含：
- Skills 的标准格式和 frontmatter
- 如何跨工具兼容（Claude Code、Codex）
- `/skill:name` 命令用法
- Skill 目录结构和最佳实践

---

### 一般查询流程

1. **`pi --help`**：CLI 参数的权威来源，一条命令秒出结果
2. **本地文档**：`read` 对应的 docs/*.md 文件和 README.md

```bash
# 定位本地文档目录
PI_DOCS=$(find ~/.local/share/pnpm -path "*/pi-coding-agent/docs" -type d 2>/dev/null | head -1)
PI_README=$(find ~/.local/share/pnpm -path "*/pi-coding-agent/README.md" -type f 2>/dev/null | head -1)

# 特别地，Skills 文档的固定位置
PI_SKILLS=~/.npm-global/lib/node_modules/pi-amplike/node_modules/@mariozechner/pi-coding-agent/docs/skills.md
```

3. **curl GitHub README**：获取最新版本的文档

```bash
curl -s https://raw.githubusercontent.com/badlogic/pi-mono/main/packages/pi-coding-agent/README.md
```

4. **grep 源码**：最后手段，文档找不到时才搜实现代码

```bash
PI_SRC=$(find ~/.local/share/pnpm -path "*/pi-coding-agent/dist" -type d 2>/dev/null | head -1)
grep -r "关键词" "$PI_SRC/" --include="*.js"
```
