---
name: my-chezmoi-jj-flow-linux
description: WeiYiAcc 的 Linux 侧 chezmoi 同步操作。jj native 流程，配 ariadne-fact 仓库内的 bb-bricks/chezmoi polylith brick（chezmoi component + chezmoi-cli base），以 `bb chezmoi:push/pull/status` 为入口。涵盖路径硬规则的两道防线、age 加密约定、exact_ 前缀、跟踪策略、个人血泪教训。触发场景：在 ~/.local/share/chezmoi/ 下操作、调用 chezmoi add/apply/push、bb chezmoi:*、ariadne-fact bb-bricks/chezmoi 相关、调试 ~/.config/chezmoi/chezmoi.toml。Windows chezmoi 库（jj 不可用、纯 git）走另一个 skill `my-chezmoi-git-flow-windows`。
---

# my-chezmoi-jj-flow-linux — WeiYiAcc 的 Linux chezmoi 同步流程

## 仓库与工具

- **chezmoi source**：`~/.local/share/chezmoi/`
- **远程**：`git@github.com:WeiYiAcc/my-dotfiles-linux.git`
- **VCS**：`jj native`（2026-08-15 起；工作区无 git 仓库，仅保留空 `.git/` 占位目录供 chezmoi 识别 worktree；不要用裸 `git commit/push`）
- **age 密钥**：`~/.config/chezmoi/key.txt`（recipient `age10ue93j9ud8kepwyaldd6c8e5g0sk0jf4lfkaz9aqv0gxqyvzjusq5f8pyt`）
- **入口（推荐）**：`bb chezmoi:status / push / pull`，实现在 `~/ghq/github.com/WeiYiAcc/ariadne-fact/bb-bricks/`

> Windows 侧仓库（`my-dotfiles-windows`）是另一套（纯 git，没 jj），见 skill `my-chezmoi-git-flow-windows`。

## 与 chezmoi-expert 的关系

通用 chezmoi 知识（命令参考、模板语法、diff 方向、文件名前缀）全部在 `chezmoi-expert` skill：

- SKILL.md — 主入口
- `references/commands.md` — 完整命令参考
- `references/common-scenarios.md` — 新机器 setup / SSH / VS Code 等
- `references/encryption.md` — age/GPG/1Password
- `references/templates-and-workflows.md` — 模板语法
- `references/troubleshooting.md` — 故障排查

skill 路径：`~/.pi/agent/git/github.com/WeiYiAcc/claude-plugins/plugins/chezmoi/skills/chezmoi-expert/`

本 skill 只包含 weiyiacc 个人的 Linux 侧约定 + ariadne-fact bb-bricks 入口。

---

## ⚠️ 进入 chezmoi source 前：确认 jj @ 在 master 最新

```bash
cd ~/.local/share/chezmoi
jj git fetch 2>/dev/null
jj rebase -d master 2>/dev/null   # 幂等，已在最新则无操作
```

不做这步会导致：看到的文件是过时的，另一台电脑 push 的内容不可见，重复修改产生冲突。

---

## 标准操作（推荐路径）

### `bb chezmoi:push [msg]` —— 完整同步

```bash
cd ~/ghq/github.com/WeiYiAcc/ariadne-fact
bb chezmoi:push                                # 默认 message: chore: sync_<ts>
bb chezmoi:push "feat: add new dotfile xxx"    # 自定义 message
```

实际链路（`af.chezmoi-cli.core/-main "push"`）：

1. `chezmoi status` → 解析变更文件列表
2. 对每个变更文件按**两道防线**决策 add 模式：
   - **第一道**：路径硬规则（`af.chezmoi.core/must-encrypt-patterns`，21 条 regex，抄自 guardrails 0.11.0）→ 已知敏感路径**强制加密**
   - **第二道**：`chezmoi add --dry-run --secrets=error` → exit 1 + stderr 含 "Detected ..." 也走加密
   - 其余 → 普通 `chezmoi add`
3. `jj commit -m <msg>` → `jj git push`（master 由 ~/.config/jj/config.toml 的 experimental-advance-branches 自动前进）
4. `chezmoi apply --force`

### `bb chezmoi:status` —— 检查变更

```bash
bb chezmoi:status
# ── chezmoi status ──
#   [MM] .config/rclone/rclone.conf
#   [MM] .pi/agent/settings.json
```

`[XY]` 格式：`X` = source 状态, `Y` = target 状态。`M`=modified, `A`=added, `D`=deleted。

### `bb chezmoi:pull` —— 拉取远端 + apply

`jj git fetch` → `jj rebase -d master@origin` → `chezmoi apply --force`

### 手动操作（兜底）

```bash
chezmoi add <file>                              # 普通明文
chezmoi add --encrypt <file>                    # 加密
chezmoi add --secrets=error <file>              # 明文 + 强制 secret 检查（exit 1 拒绝）
cd ~/.local/share/chezmoi
jj commit -m "..." && jj git push（master 自动前进）
chezmoi apply --force
```

**注意**：bb 包装脚本和这里的手动操作**不能混用** ——bb 已经把 add 全自动化（含决策），别同时手动 add。

---

## 加密决策（两道防线）

### 第一道：路径硬规则

代码：`bb-bricks/components/chezmoi/src/af/chezmoi/core.clj` 的 `must-encrypt-patterns`，21 条 regex，覆盖：

| 类别 | 模式 |
|---|---|
| dotenv | `.env` / `.env.*` / `.dev.vars` / `*-deploy/.env` |
| SSH | `.ssh/**` / `*_rsa` / `*_ed25519` / `*.pem` |
| AWS | `.aws/credentials` / `.aws/config` |
| GnuPG | `.gnupg/**` / `*.gpg` |
| Kubernetes | `.kube/config` / `*kubeconfig*` |
| 证书 | `*.crt` / `*.key` / `*.p12` |
| 数据库 | `*.db` / `*.sqlite` / `*.sqlite3` |
| pi 配置 | `.pi/agent/(models\|auth).json` |
| rclone | `rclone.conf` |
| pi sessions | `sessions/*.jsonl` |

**模式来源**：`@aliou/pi-guardrails@0.11.0` 的 `docs/defaults.md` 和 `docs/examples.md`。同步上游版本时记得回头审视这份列表。

### 第二道：chezmoi 内置 trufflehog detector

`chezmoi add --dry-run --secrets=error` 返回 exit 1 时认为是 sensitive。

⚠️ **chezmoi 默认 `--secrets=warning` 只警告不拦截**，必须显式 `--secrets=error` 才有效。我们 brick 永远用 `error` 模式。

### 加密的实际效果

`chezmoi add --encrypt`：
- 目标未加密 → **升级**为 `encrypted_<name>.age`
- 目标已加密 → **保持**加密形态（diff 显示密文整体变化是因为每次加密 nonce 不同，正常）

不需要 `chezmoi forget` 再 add，直接 `add --encrypt` 就能正确处理两种情形。

---

## 跟踪策略

### 全量跟踪 + 单层 .gitignore

- **source 里有的就是要同步的**，不想同步的就不放进 source
- 只维护一层忽略：`.gitignore`
- `.chezmoiignore` **留空**备用
- **弃用/过时的配置也跟踪**（vcsh/yadm.legacy/ruby_dev/lvim 等），统一手动清理
- **不要擅自不添加任何文件** — 即使觉得过时，也先 add，让用户手动决定

### .gitignore 只排除三类

```
.jj/                       # jj native 内部目录
dot_pi/agent/git/          # pi 包缓存（~1.2GB，机器自动下载）
dot_config/starship.toml   # nix/home-manager 生成的软链接
```

### chezmoi 自身配置由 yadm 管理

chezmoi 禁止 `chezmoi add ~/.config/chezmoi/` — 保护自己的配置目录。`chezmoi.toml` + `key.txt` 由 **yadm 作为前置依赖**部署：

```bash
# 新机器部署顺序：
yadm clone <repo>                                            # 1. 部署 chezmoi.toml + key.txt
chezmoi init git@github.com:WeiYiAcc/my-dotfiles-linux.git   # 2. chezmoi init
chezmoi apply                                                 # 3. 部署所有 dotfiles
```

### `~/.config/` 全量跟踪

所有 `.config/` 子目录都 `chezmoi add`（包括弃用的）。例外：nix 生成的**软链接**（`.gitignore` 排除）和 `chezmoi/` 自身。

---

## ⚠️ exact_ 前缀（血泪教训）

chezmoi 默认**不会删除**磁盘上不再在 source 里的文件。从 source 删文件后 `chezmoi apply` → 磁盘残留。

**已应用 `exact_` 前缀的目录**（`chezmoi apply` 自动清理不在 source 里的残留文件）：

| chezmoi source 目录名 | 磁盘目录 |
|---|---|
| `dot_pi/agent/exact_extensions` | `~/.pi/agent/extensions/` |
| `dot_pi/agent/exact_lib` | `~/.pi/agent/lib/` |
| `dot_pi/agent/exact_skills` | `~/.pi/agent/skills/` |
| `dot_pi/agent/exact_skills-bench` | `~/.pi/agent/skills-bench/` |
| `dot_pi/agent/exact_skills-disabled` | `~/.pi/agent/skills-disabled/` |

**规则**：对必须严格和 source 一致的目录，**必须**用 `exact_` 前缀。

**教训**：不加 `exact_` 时，拆分全局/项目级 extension 后另一台电脑 `chezmoi apply` 残留旧文件 → symphony tool 冲突。

**添加新 exact_ 目录**：`cd ~/.local/share/chezmoi && mv dirname exact_dirname`

**决策源**：fact `chezmoi-exact-prefix-for-strict-sync`

---

## 全局 vs 项目级 .pi 分拆（2026-04-12）

pi-mono 的 extensions 现在分两层：

| 层 | 位置 | 内容 | 由谁管理 |
|---|---|---|---|
| 全局 | `~/.pi/agent/extensions/` | 通用 extensions（my-env-loader、my-role、my-todo-panel、multi-edit 等） | chezmoi（`exact_extensions`） |
| 项目级 | `<project>/.pi/extensions/` | 项目专属 extensions | 项目自己的 git 仓库 |

ariadne-fact 项目级：`~/ghq/github.com/WeiYiAcc/ariadne-fact/.pi/extensions/workspace-loader.ts`（polylith bricks 的 jiti 加载器）。

**不要**把项目专属 extension 放回全局——会导致 tool 冲突（如 `Tool "symphony" conflicts`）。

---

## Linux 侧 jj push 流程（手动版）

**重要**：source tree 用 **jj**（不是纯 git）。不要用 `git commit/push`：

```bash
# 1. add 变更（建议直接 bb chezmoi:push 自动化）
chezmoi add <file>

# 2. 切到 source dir
cd ~/.local/share/chezmoi

# 3. jj commit
jj commit -m "<description>"

# 4. master bookmark 指到最新 commit 的父（jj 的 @ 是 working copy）
jj bookmark set master -r @-

# 5. push
jj git push
# （native 模式无需修复 detached HEAD）
```

### 常见错误

**`Non-tracking remote bookmark master@origin exists`**：
```bash
jj bookmark track master --remote=origin
# 然后重试步骤 4-6
```

详见 skill `my-jj`（如果存在）。

### ⚠️ 强制规则：任何配置修改后必须 chezmoi status

**无论改了什么配置文件（nix、pi settings、skill、bb.edn 等），改完第一件事是 `chezmoi status`**，确认变更是否已反映到 source，以及是否需要 `chezmoi add` + push。

这能防止：
- 改了磁盘忘记 add → 另一台电脑 pull 时覆盖掉
- 以为 source 有实际没有 → 下次 apply 回滚
- 多台电脑同时改同一文件 → bisync conflict

### 何时要 push Linux 侧

- `~/.pi/agent/models.json` / `settings.json` 变更
- `~/home-manager/home_wsl.nix` + `home-manager switch` 成功后（**每次 switch 后都要 push**，无论是否改 .nix——switch 会重建 symlinks）
- `~/.claude/settings.json` 变更
- 本 skill 或其他 skill 变更时（`~/.pi/agent/skills/` 在 chezmoi 管理下）
- `~/.pi/agent/extensions/` 变更时（全局 extensions 由 chezmoi 管理，`exact_` 目录）
- `~/bb.edn` 变更时（全局 bb 任务入口）

**AGENTS.md 硬规则**：每次 `home-manager switch` 成功后必须立刻 chezmoi add + jj push（用 `bb chezmoi:push`）。

---

## age encryption 约定

`~/.config/chezmoi/chezmoi.toml`：

```toml
encryption = "age"
[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age10ue93j9ud8kepwyaldd6c8e5g0sk0jf4lfkaz9aqv0gxqyvzjusq5f8pyt"
```

### 关键坑：chezmoi.toml 不是模板

除非文件名带 `.tmpl` 后缀，否则 chezmoi.toml **不会展开模板**。**不要**在 identity 字段写 `{{ keepassxc "..." }}` 之类——chezmoi 会把字面量当文件路径打开，报"no such file"。

**决策源**：fact `chezmoi-toml-identity-field-is-not-template`

### age 私钥的安全规则

**禁用命令**（会把私钥明文写进 AI session 日志）：`cat`, `head`, `tail`, `less`, `more`, `rg '.+' <file>`

**安全查看**：
- `ls -la ~/.config/chezmoi/key.txt` — 看权限时间戳
- `wc -c ~/.config/chezmoi/key.txt` — 合法 age 私钥是 75 字节（单行 + newline）
- `age-keygen -y ~/.config/chezmoi/key.txt` — 派生 public key（可安全显示）
- `head -1 ~/.config/chezmoi/key.txt | grep -q "^AGE-SECRET-KEY-" && echo OK` — 只验证格式

**决策源**：fact `secrets-handling-in-session-logs`

---

## 命令速查

| 场景 | 命令 |
|---|---|
| 推荐：完整同步 | `cd ~/ghq/github.com/WeiYiAcc/ariadne-fact && bb chezmoi:push [msg]` |
| 推荐：拉取远端 | `cd ~/ghq/github.com/WeiYiAcc/ariadne-fact && bb chezmoi:pull` |
| 推荐：检查变更 | `cd ~/ghq/github.com/WeiYiAcc/ariadne-fact && bb chezmoi:status` |
| 手动 add | `chezmoi add <f>` / `chezmoi add --encrypt <f>` |
| 看完整 diff | `chezmoi diff` —— 慎用，详见 chezmoi-expert SKILL.md |
| 加密新文件 | `chezmoi add --encrypt <f>` |
| 解密查看 | `chezmoi cat <f>` |
| 编辑加密文件 | `chezmoi edit <f>` |
| doctor 检查 | `chezmoi doctor` |
| chezmoi 不识别的改动 | `chezmoi re-add <f>` —— 但模板文件（`.tmpl`）禁用！且 **`re-add` 不支持 `--secrets` flag**，敏感文件请用 `add`（chezmoi 对已托管文件 add 时会替换 source state） |

---

## 相关 Ariadne facts

- `chezmoi-secrets-flag-behavior` — chezmoi 内置 secret detection 的 trufflehog 启发式实战边界
- `chezmoi-tracking-strategy-full-gitignore` — 全量跟踪 + 单层 .gitignore（当前策略）
- `chezmoi-exact-prefix-for-strict-sync` — exact_ 前缀血泪教训
- `dual-chezmoi-architecture-linux-and-windows` — 双仓库架构决策
- `chezmoi-toml-identity-field-is-not-template` — identity 字段陷阱
- `yadm-bootstrap-for-chezmoi` — yadm 作为 chezmoi 前置依赖
- `secrets-handling-in-session-logs` — 私钥安全操作
- `chezmoi-reAdd-and-encrypt-sensitive` — 实体文件变动必须手动 re-add，敏感文件应加密
- `pi-cli-skill-discovery-mechanism` — pi 发现 skill 机制
- `my-repo-sync` — 仓库同步工具

## 相关代码

- `~/ghq/github.com/WeiYiAcc/ariadne-fact/bb-bricks/components/chezmoi/` — 决策算法（纯函数）
- `~/ghq/github.com/WeiYiAcc/ariadne-fact/bb-bricks/bases/chezmoi-cli/` — CLI 入口（副作用）
- `~/ghq/github.com/WeiYiAcc/ariadne-fact/bb.edn` — `chezmoi:status/push/pull` task 定义
