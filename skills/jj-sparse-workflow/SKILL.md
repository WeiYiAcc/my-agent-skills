---
name: jj-sparse-workflow
description: >
  jj workspace + sparse patterns + forklift 的 monorepo 协作工作流。
  涵盖：为子目录创建专用工作区、用 jj sparse set 聚焦磁盘空间、
  forklift 提交和同步堆栈 PR。触发场景：在 monorepo 里为 sec-cell/sec
  等子目录创建工作区、用 sparse set 减少磁盘占用、forklift 提交流程。
---

# jj Monorepo 工作流

## 核心纪律

**jj sparse set 只影响工作目录视图，不写入 jj operation log，也不影响 forklift 提交。**
两者完全兼容，可安全组合使用。

## 工作区创建

### 1. 创建专用工作区

```bash
# 在主仓库创建 sec-cell 专用工作区
jj workspace add ../sec-cell-work --name sec-cell

# 进入工作区
cd ../sec-cell-work

# 设置稀疏模式，只保留 sec-cell/ 目录
jj sparse set "sec-cell/**"
```

### 2. 验证稀疏模式

```bash
# 查看当前稀疏模式
jj sparse list

# 确认只看到 sec-cell/ 目录
ls
```

### 3. 切换/重置

```bash
# 回到全量
jj sparse set --reset

# 重新聚焦
jj sparse set "sec-cell/**"
```

## 提交和 PR 流程

### 在任意工作区提交（推荐在主仓库工作区）

```bash
# 1. 检查状态（所有工作区的改动都在同一 jj 仓库）
jj status

# 2. 写描述
jj describe --message "feat: 描述改动"

# 3. 新提交
jj new

# 4. fork + submit（自动创建 PR）
~/.cargo/bin/forklift submit --yes

# 5. 同步（清理栈、同步远程）
~/.cargo/bin/forklift sync

# 6. 合并 PR（可选）
gh pr merge <n> --merge --delete-branch
```

## 目录结构约定

```
slate-effect-cli/                    ← 主仓库（jj colocate）
├── .jj/                            ← 共享的 jj 仓库元数据（所有工作区共享）
├── src/                            ← SEC CLI 源码
├── sec-cell/                       ← celld + AgentOS 集成
├── .sec-tasks/                     ← 任务跟踪
└── ../sec-cell-work/               ← 专用工作区（稀疏）
    └── (只 checkout sec-cell/**)   ← jj sparse set 生效
```

## 与 forklift 的兼容性

| 操作 | 影响范围 | 对 forklift |
|------|---------|------------|
| `jj sparse set` | 工作目录视图（磁盘文件） | **无影响** — forklift 只读 jj operation log |
| `jj workspace add` | jj 元数据（共享 .jj/） | **无影响** — 工作区只是指针 |
| `jj new/describe/squash` | jj operation log | **有影响** — forklift 读取这些操作 |
| `forklift submit` | GitHub PR + bookmark | **有影响** — 推送到远程 |

## 常见陷阱

### 1. forklift 不在 PATH
```bash
~/.cargo/bin/forklift submit --yes   # 用完整路径
```

### 2. `.celld/dev/` 和 `node_modules/` 不应进入提交
确保 `.gitignore` 包含：
```
.celld/dev/
node_modules/
```

### 3. 工作区落后 trunk
```bash
# 检查
jj log -r "@-"   # 工作区 @
jj log -r "trunk()"  # 主线

# 落后则 rebase
jj rebase -d master
```

## 与 chezmoi 的关系

- `jj` 管理**源码**（src/、sec-cell/ 等）
- `chezmoi` 管理**配置**（~/.config/、~/.local/bin/ 等）
- 两者正交，互补，不要混淆

## 参考

- `jj sparse --help`
- `jj workspace --help`
- `~/.cargo/bin/forklift --help`
