---
name: my-jj
description: "Use jj (Jujutsu) for version control in all repositories (all repos are jj colocate; GitButler/but is retained only for special scenarios). Activate when: version control operations are needed in any repo, or the user explicitly says 'use jj'. Do NOT use git write commands (git add/commit/push/stash) in jj repos."
---

# jj (Jujutsu) — Version Control for Agent Workflows

jj is a version control tool that coexists with Git. You use jj locally; the remote is still standard Git. GitHub and collaborators see ordinary git commits and branches.

This skill teaches you how to use jj correctly and idiomatically, especially in agent-assisted development workflows.

## ⚠️ 强制前置规则（每次操作代码后）

**任何代码修改完成后，必须按以下顺序执行：**

```bash
# 1. 检查 chezmoi 状态（确认修改不需要 chezmoi add）
chezmoi status
# 如果有输出 → 说明改到了 chezmoi 管理的文件，先 chezmoi add + push

# 2. jj commit
jj commit -m "描述"
# 如果报错 "There is no jj repo" 或类似 → 立刻提醒用户：当前目录不是 jj 仓库！
```

**如果 `jj commit` 报错或结果为空（no changes），必须立刻告知用户**，不能静默跳过。可能原因：
- 不在 jj 仓库里（缺 `.jj/` 目录）
- 文件改动在 working copy 之外

## ⚠️ 每次进入仓库时：确认 @ 在 trunk 最新

**开始工作前必须检查 working copy 是否在 trunk（master/main）最新位置：**

```bash
jj log -r "@-" -T 'commit_id.short()'    # 查看 parent
jj log -r "trunk()" -T 'commit_id.short()' # 查看 trunk
# 如果不一致 → rebase
jj rebase -d master
```

**为什么这很重要：** 如果 @ 落后 trunk，你看到的文件内容是过时的（另一台电脑 push 的改动不可见），会导致重复修改和冲突。

**常见场景：**
- `jj git fetch` 拉取了远端新 commit，但没有 rebase
- 刚 `jj git init --colocate` 的仓库，@ 已经在最新，不需要操作
- 长时间没操作的仓库，可能落后很多 commit

---

## Core Mental Model

jj revolves around **changes**, not branches. Key differences from Git:

- **No staging area.** File modifications are automatically part of the current change. There is no `git add`.
- **No stash.** Just `jj new` to start fresh work; previous changes stay where they are.
- **No detached HEAD.** `jj edit` lets you jump to any change and keep working; descendants auto-rebase.
- **Branches are called bookmarks** and are only needed when pushing to a remote.

The working copy IS a change. Every file modification is instantly tracked in the current change.

## Detecting a jj Repo

Before performing version control operations, check if the repo uses jj:

```bash
# If .jj/ exists, use jj commands — not git commands
test -d .jj && echo "jj repo"
```

When a repo has both `.jj/` and `.git/` (colocated mode), always prefer jj commands for local operations.

## Setup

To initialize jj in an existing Git repo (colocated mode — keeps `.git/` alongside `.jj/`):

```bash
jj git init --colocate
```

After init, you may need to track remote bookmarks so jj knows about remote branches:

```bash
jj bookmark track master@origin        # Track a specific remote branch
```

jj will usually hint you about this if it's needed.

## Essential Commands

### Inspect State

```bash
jj log                    # Show change graph + status (replaces git log + git status)
jj diff                   # Show diff of current change vs parent
jj diff -r <change>       # Show diff of a specific change
```

`jj log` output shows `@` for the current change and short Change IDs (e.g., `kxryzmsp`). Change IDs are stable across rebases — use them freely as references. You can use unique prefixes (e.g., `kx` instead of `kxryzmsp`) as long as they are unambiguous.

### Work on Changes

```bash
jj describe -m "feat: add auth module"   # Set/update description of current change
jj describe -r <change> -m "new msg"     # Update description of any change
jj new                                    # Finish current change, start a new empty one
jj new <change>                           # Start new work branching from a specific change
jj commit -m "feat: ..."                  # Shorthand: describe current + start new (equivalent to describe + new)
jj edit <change>                          # Jump to an existing change and continue editing it
jj abandon                                # Discard the current change entirely
jj abandon <change>                       # Discard a specific change
```

**`jj new` is your primary "next task" command.** It seals the current change and gives you a fresh workspace. No add, no commit ceremony.

**`jj abandon`** discards a change completely. The change's modifications are absorbed into its parent. Use it to clean up empty changes, throw away unwanted work, or remove a change from a chain.

**`jj edit` is safe:** if the target change is immutable (already pushed to remote), jj will refuse with an error. You do not need to check this yourself.

After `jj edit`, modifying files amends that change in place. All descendant changes auto-rebase — you never need to manually rebase after editing an ancestor.

### Reorganize History

```bash
jj split                                 # Interactively split current change into two (or more)
jj split -r <change>                     # Split a specific change
jj rebase -s <source> -d <destination>   # Move a change (and its descendants) to a new parent
jj rebase -d <destination>               # Rebase current branch onto destination
jj undo                                  # Undo the last jj operation (any operation)
jj op log                                # View operation-level history
jj op restore <operation-id>             # Restore repo to any previous operation state
```

`jj split` opens an interactive editor by default (when no filesets are given). Select which files/hunks belong to the first change; the rest automatically become the second. Repeat to split further.

`jj undo` undoes the last operation regardless of what it was — rebase, split, describe, anything. It is always safe. Nothing is ever truly lost in jj.

### Remote Interaction (Git Bridge)

```bash
jj git fetch                             # Fetch from remote (like git fetch)
jj rebase -d master                      # Rebase current work onto latest master
jj bookmark track master@origin          # Track a remote branch (needed after init or for new remotes)
jj bookmark create my-feature -r @       # Create a bookmark (= git branch) pointing at current change
jj bookmark create my-feature -r <chg>   # Create a bookmark pointing at a specific change
jj bookmark set my-feature -r <change>   # Move an existing bookmark to a different change
jj git push                              # Push all changed bookmarks to remote
jj git push --bookmark my-feature        # Push only a specific bookmark
jj git push --deleted                    # Push bookmark deletions to remote (after jj abandon)
```

Remote Git branches are automatically mapped to jj **bookmarks** on fetch. The `master` (or `main`) you see in `jj log` IS the remote branch, accessed via bookmark.

After `jj git init --colocate` or when a new remote branch appears, you may need `jj bookmark track <name>@<remote>` to tell jj to follow it. jj will hint you when this is needed.

**Workflow for pushing:**
1. Finish your work (describe the change)
2. `jj bookmark create <name> -r <change>` — give it a Git branch name
3. `jj git push` — push to remote (or `--bookmark <name>` for just one)

**Workflow for pushing to `master` in colocated repos (most common case):**

After `jj commit`, git HEAD will be detached. Always follow these steps:

```bash
jj commit -m "your message"              # 1. 提交
jj bookmark set master -r @-            # 2. 移动 master bookmark 到刚提交的位置
jj git push --bookmark master           # 3. 推送
git checkout master                     # 4. 修复 git detached HEAD（必须！）
```

Short form (bookmark + push + fix HEAD in one line):
```bash
jj bookmark set master && jj git push --bookmark master && git checkout master
```

> Note: If `master@origin` is not yet tracked, run `jj bookmark track master --remote=origin` once first.

## ⚠️ Colocate 仓库的 git HEAD 漂移问题

**问题**：jj colocate 仓库中，jj 操作（commit/rebase/edit）会导致 git HEAD detached，`git log` 显示的不是最新 commit，扩展和工具读取 git HEAD 时拿到旧数据。

**规则：每次 jj 操作后必须运行 `git checkout master`**（或 `main`）：

```bash
# 每次 jj commit / jj bookmark set / jj git push 之后
git checkout master
```

**检查是否漂移：**
```bash
git status | head -1   # 如果显示 "HEAD detached at ..." 说明已漂移
```

**修复漂移：**
```bash
git checkout master
```

这不是 jj bug，是 colocate 模式的已知行为。官方无计划修复，社区 workaround 是手动 `git checkout master`。

**Cleanup after abandoning a pushed change:**
When you `jj abandon` a change that had a bookmark pushed to remote, the bookmark is deleted locally. Use `jj git push --deleted` to sync that deletion to the remote.

### Parallel Workspaces

```bash
jj workspace add ../workspace-name       # Create a parallel workspace (like git worktree)
```

Each workspace gets its own directory but shares the underlying repository store. Multiple agents can work in separate workspaces simultaneously from the same base, then merge results with `jj new <change1> <change2> ...`.

## Agent Workflow Patterns

These patterns leverage jj's strengths for agent-assisted development.

### Pattern 1: Start Next Task

Just `jj new` and begin. No need to add, commit, push, or create a branch first. The previous change is automatically preserved.

```bash
jj new
jj describe -m "feat: implement avatar upload"
# start working...
```

### Pattern 2: Interrupt and Resume

To handle an urgent task mid-work:

```bash
jj new master            # Branch off master for the urgent fix
# ... do the fix ...
jj describe -m "fix: critical auth bug"
jj edit <previous-change> # Jump back to where you were
# ... resume previous work ...
```

No stash, no branch switching, no state to restore.

### Pattern 3: Split After the Fact

After producing a large change, split it into logical pieces:

```bash
jj split                 # Interactive: pick files/hunks for first change, rest goes to second
jj split                 # Split again if needed
```

If a split goes wrong, `jj undo` and try again.

### Pattern 4: Skeleton Planning (Recommended for Complex Tasks)

Create empty changes as a plan, then fill them in order:

```bash
jj commit -m "refactor: extract auth module"
jj commit -m "feat: add token refresh logic"
jj commit -m "test: update auth tests"
jj commit -m "docs: update API documentation"
```

Then work through them:

```bash
jj edit <first-change>   # Jump to first skeleton change
# ... implement ...
jj edit <next-change>    # Jump to next (previous work auto-rebases descendants)
# ... implement ...
```

Each change's description serves as both the commit message and the acceptance criteria. Verify your implementation matches the description before moving on.

The description field supports the same format as git commit messages: first line is the title, blank line, then body. You can write detailed specs or prompts in the body with `-m`.

### Pattern 5: Undo and Recover

```bash
jj undo                  # Undo last operation, no questions asked
jj op log                # See full operation history if you need to go further back
jj op restore <op-id>    # Jump to any point in operation history
```

Prefer `jj undo` over trying to manually reverse changes. It is always correct and safe.

## Conflict Resolution

jj stores conflicts as **structured 3-way data** (not text markers like `<<<<<<<`):
- `base`: common ancestor content
- `side_1`: one side's changes
- `side_2`: other side's changes

When resolving conflicts as an agent:
1. Edit the conflicted file directly — remove conflict markers and write the merged result
2. Use the **change descriptions** of both sides as intent context to decide how to merge
3. `jj st` to verify conflict markers are gone — descendants auto-rebase after resolution

```bash
# Check which changes have conflicts
jj log   # conflicted changes are marked with ⚠

# Jump to conflicted change
jj edit <change-id>

# Edit file to resolve (remove markers, write correct merge)
# jj auto-detects resolution and propagates to descendants
```

**Key advantage over git**: conflict resolution in an ancestor change automatically propagates to all descendants. You don't need to resolve the same conflict repeatedly.

## Multi-Agent Parallel Workspaces

Each workspace has exactly **one state**: its `@` change ID. This makes orchestration simple — tracking N parallel agents = tracking N change IDs.

```bash
# Create isolated workspace per agent/task
jj workspace add ../feature-auth
jj workspace add ../bugfix-login

# Each workspace has its own @ — no branch locking, no shared index
jj workspace list

# When done: clean up
jj workspace forget feature-auth
rm -rf ../feature-auth
```

Use cases:
- Run tests in one workspace while coding in another
- Multiple agents working on different issues simultaneously
- Compare file states across different revisions

For the conceptual background on why jj fits the agent era, see the `jj-agent-era-concepts` fact.

## Common Mistakes to Avoid

- **Do not use `git add`, `git commit`, `git stash`, or `git checkout` in a jj repo.** Use jj equivalents instead.
- **`jj split` is interactive and will hang in agent environments.** Use `jj restore --from @- <path>` to move files out instead.
- **Do not try to `jj edit` an immutable (published) change** without good reason. jj will block this. If you need to fix something in published history, use `jj new <change>` to create a follow-up change instead.
- **Do not create bookmarks for local-only work.** Bookmarks are only needed when pushing to remote. Local work is tracked by Change IDs.
- **Do not worry about "losing" changes.** jj's operation log preserves everything. Use `jj undo` or `jj op restore` to recover from any mistake.

## Stacked PRs with forklift

`forklift` 是 jj-native 的 stacked PR 工具（fork: `WeiYiAcc/jj-forklift`，二进制在 `~/.local/bin/forklift`）。

```bash
# 提交一组 stacked changes 为 GitHub PRs（每个 change 一个 PR）
forklift submit

# 查看当前 stack 状态
forklift status
```

**前置条件：**
- 仓库有 `.jj/` 目录（jj colocate）
- `gh auth status` 已登录（token 需要 `repo` scope）
- 每个 change 有 description（`jj describe -m "..."` 设置）

**典型工作流：**
```bash
jj commit -m "feat: step 1"
jj commit -m "feat: step 2"
jj commit -m "feat: step 3"
forklift submit          # 一键提交 3 个 stacked PR
```

**更新已有 PR（在 review 后修改）：**
```bash
jj edit <change-id>      # 跳到需要修改的 change
# ... 修改文件 ...
forklift submit          # 重新提交，自动更新对应 PR
git checkout master      # 修复 git HEAD
```

## Quick Reference

| Task | jj command |
|------|-----------|
| Initialize in existing git repo | `jj git init --colocate` |
| See what's going on | `jj log` |
| Describe current change | `jj describe -m "..."` |
| Start next task | `jj new` |
| Branch from specific change | `jj new <change>` |
| Edit an older change | `jj edit <change>` |
| Discard a change | `jj abandon` / `jj abandon <change>` |
| Split a change | `jj split` |
| Undo anything | `jj undo` |
| Fetch remote | `jj git fetch` |
| Track a remote branch | `jj bookmark track <name>@<remote>` |
| Rebase onto master | `jj rebase -d master` |
| Create bookmark for push | `jj bookmark create <name> -r @` |
| Move existing bookmark | `jj bookmark set <name> -r <change>` |
| Push to remote | `jj git push` |
| Push specific bookmark | `jj git push --bookmark <name>` |
| Push bookmark deletions | `jj git push --deleted` |
| Merge multiple changes | `jj new <chg1> <chg2> ...` |
| Parallel workspace | `jj workspace add <path>` |

## Beyond This Skill

This skill covers the most common operations. For advanced usage not covered here, use:

```bash
jj help                  # List all commands
jj help <command>        # Detailed help for a specific command
jj help -k <keyword>     # Search help by keyword
```

jj has rich functionality (revsets, templates, custom aliases, conflict resolution, etc.) that you can explore via `jj help` and apply based on the situation. The official documentation is at https://jj-vcs.github.io/jj/.
