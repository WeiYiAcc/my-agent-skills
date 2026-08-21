---
name: stokowski
description: "用 Stokowski（fork of Sugar-Coffee/stokowski）编排 Claude Code / Codex 子代理。两种 tracker：Linear issue 驱动 或 local file-based（yaml task 文件）。状态机自动推进 investigate → review → implement → review → code-review → done，含人工 gate 和对抗式 review。仓库 ~/ghq/github.com/WeiYiAcc/stokowski/。当需要多步骤工作流 + 人工审核 + 多 runner 第二意见时使用。"
---

# Stokowski

**定位**：Stokowski 是 OpenAI Symphony spec 的扩展实现，**Python daemon**，把 Linear issue（或本地 yaml 文件）当作任务源，自动驱动 Claude Code / Codex CLI 走完"调研→人工审核→实现→人工审核→对抗式 code review→merge"的状态机。

**Fork 关系**：
- 上游：`github.com/Sugar-Coffee/stokowski`
- 你的 fork：`github.com/WeiYiAcc/stokowski`（含 `local_tracker.py` 等本地化改造）
- 上游待办 **issue #18**：请求 pluggable runner interface，让 Stokowski 能调 Pi（pi-coding-agent）或 Hermes 而不只是 Claude Code/Codex

## 状态机概览

```
Linear Issue (Todo) | 或 local task yaml file
  → investigate (Claude Opus)
  → research-review [GATE: 人工]
  → implement (Claude Sonnet)
  → implementation-review [GATE: 人工]
  → code-review (Claude Opus / Codex 第二意见)
  → merge → Done
```

## 仓库位置

- 源码：`~/ghq/github.com/WeiYiAcc/stokowski/`
- 二进制：**未全局安装**，必须用 `python -m stokowski` 或 `uv run stokowski`
- 入口：`stokowski/main.py:cli()`

## 安装与启动

```bash
cd ~/ghq/github.com/WeiYiAcc/stokowski

# 首次安装（已完成）
uv pip install -e .

# 验证
uv run stokowski --help
```

## 调用方式

Stokowski 跑的是仓库根的 `workflow.yaml` + `prompts/*.md`（上游约定，operator-local，gitignored）。fork 提供三套 yaml 模板 + 三套 prompts 候选目录，**用前先 cp**。

### 三套候选

| 流水线 | yaml 模板 | prompts 候选 | tracker | gate | 适用 |
|---|---|---|---|---|---|
| **linear-full-auto** | `workflow.linear-full-auto.yaml` | `prompts_linear-full-auto/` | Linear | 无 | 简单功能、信任 agent |
| **linear-half-auto** | `workflow.linear-half-auto.yaml` | `prompts_linear-half-auto/` | Linear | 2 道 gate | 高风险、要人工审 |
| **local-full-auto** | `workflow.local-full-auto.yaml` | `prompts_local-full-auto/` | local file | 无 | 离线、私密、测试 |

### 启动步骤（三套通用）

```bash
cd ~/ghq/github.com/WeiYiAcc/stokowski

# 0. 设置 STOKOWSKI_REPO_ROOT（yaml 里 $STOKOWSKI_REPO_ROOT 都来自这里）
export STOKOWSKI_REPO_ROOT="$(pwd -P)"
# 也可以放进 .envrc + direnv 里自动加载

# 1. 选一套 prompts 拷进 prompts/（覆盖之前的）
rm -f prompts/global.md prompts/investigate.md prompts/implement.md prompts/review.md
cp prompts_linear-full-auto/*.md prompts/

# 2. 拷对应 yaml 到根目录覆盖 workflow.yaml
cp workflow.linear-full-auto.yaml workflow.yaml

# 3. 编辑 workflow.yaml，填两个真实值：
#    - TARGET_REPO（hooks 里两处："$HOME/ghq/github.com/your-org/your-target-repo"）
#    - tracker.project_slug（Linear 模式才有，local 模式不用）
#    确认 env：LINEAR_API_KEY (Linear) + STOKOWSKI_REPO_ROOT（步骤 0）

# 4. 启动
stokowski workflow.yaml                         # 标准启动
stokowski workflow.yaml --port 8080             # 带 web dashboard
stokowski workflow.yaml --dry-run               # 验证配置 + 列候选 issue
stokowski workflow.yaml --verbose               # debug 日志
```

`workflow.yaml` 和 `prompts/*.md` 是 gitignored 的 operator-local 副本，**不会进 jj/git**。修改它们不会污染仓库。

### 运行时数据位置

stokowski daemon 跑出来的所有运行时数据都在仓库内：

```
<stokowski-root>/agent-state/                 # 整个目录 gitignored
├── stokowski-workspaces/{auto,half-auto,local}/<issue-id>/
│       per-issue jj workspace（被 after_create 改造）
│       agent cwd 就在这里
├── stokowski-results/{auto,half-auto,local}/<issue-id>/
│       before_remove 留下的工作副本归档
├── stokowski-logs/<issue>-<ts>.log
│       手动 nohup 重定向（如果你用 nohup 启动）
└── stokowski-tasks/auto/*.yaml
        local 模式才有，每个 yaml = 一个 task
```

agent 在 workspace 里时，可以通过 `$STOKOWSKI_REPO_ROOT/references/polylith.md` 等绝对路径读 stokowski 仓库内的参考资料（global.md 已经写好了引导）。

### 仓库 VCS：jj（colocate 模式）

stokowski 已 colocate jj 上 git。所有改动走 jj 流程：

```bash
jj status
jj commit -m "..."
jj bookmark set main -r @-
jj git push --bookmark main
git checkout main           # 修复 detached HEAD
```

不要用裸 `git add/commit/push`。详见 my-jj-flow-linux skill（自动激活）。

### 模板维护

- `workflow.linear-full-auto.yaml` 等三个候选 yaml **公开 tracked**（含占位符 `your-org/your-target-repo` / `your-linear-project-slug`）
- `prompts_linear-full-auto/` 等三个候选目录 **公开 tracked**（4 个文件，目前三套内容相同，未来可分化）
- `prompts/*.example.md` 和 `prompts/*.tournament.example.md` 是上游/fork 的最原始模板

切流水线只需重跑步骤 1-2-3-4。

**配置已就绪（运行前确认）：**
- Linear API key 在 shell user profile（环境变量 `LINEAR_API_KEY`）
- Linear project slug 已知：`df340bedf106`（stokowski-auto 项目）

**使用流程：**
1. 在 Linear 创建 issue（project: stokowski-auto，状态设为 Todo）
2. 启动 stokowski，它自动拾取 Todo issue 并开始编排

**workspace 机制：** stokowski daemon 在 `workspace.root`（`$STOKOWSKI_REPO_ROOT/agent-state/stokowski-workspaces/<mode>/`）下为每个 issue 创建隔离子目录，`after_create` hook 调用 `jj workspace add` 把它改造成目标仓库（TARGET_REPO）的独立 jj workspace。agent 在隔离 workspace 里工作，commit 共享目标仓库的底层 .jj/repo。

**Linear API key 加载优先级：**
1. workflow.yaml 里 `tracker.api_key` 直接写值
2. workflow.yaml 里 `tracker.api_key: $VAR_NAME` 引用环境变量
3. fallback: 环境变量 `LINEAR_API_KEY`
4. `.env` 文件（stokowski 启动时自动 load，cwd 下的 `.env`）

## 两种 tracker

### 1. Linear（上游默认）
`tracker.kind: linear` + Linear API key + project_slug。Stokowski 在 issue 评论里写 hidden 状态标记，人工通过切换 Linear 状态来 approve/reject gate。

### 2. Local file-based（你 fork 自加，已合并到 main）
`tracker.kind: local` + `tasks_dir: ~/path/to/tasks/`。每个 task 是一个 yaml 文件，drop-in 替代 LinearClient（fetch/update/comment 全走文件）。

workflow.yaml 用：

```yaml
tracker:
  kind: local                    # 替代 linear
  tasks_dir: ~/ghq/github.com/WeiYiAcc/ariadne-fact/stokowski-tasks/
```

每个 task 文件的 yaml schema 抄 `local_tracker.py` 里的 `LocalTask` 定义。

## 替代方案对比

| 不想用 Stokowski 时 | 怎么办 |
|---|---|
| 一次性子任务，不需要状态机 | `pi subagent worker` |
| 多 worker 并行执行 | `pi-coordination` |

## 与 Overstory 的对比

| 维度 | Stokowski | Overstory |
|---|---|---|
| **范式** | **流水线**：一个 issue 一个 worker，按状态机推进 | **竞赛+审查**：多 worker 同时做，reviewer 选最优 |
| **适用** | 长周期、有人工 gate、需要稳定推进的功能开发 | 不确定方案、需要多角度方案对比的探索性工作 |
| **资源** | 1 worker × n stages | n workers × 1 stage |

## 必备配置：workflow.yaml

完整示例见 `~/ghq/github.com/WeiYiAcc/stokowski/workflow.example.yaml`。最小可用配置：

```yaml
tracker:
  kind: linear
  project_slug: "abc123def456"          # 从 Linear project URL 提取的 hex slugId
  api_key: "lin_api_xxx"                # Linear API key

linear_states:
  todo: "Todo"
  active: "In Progress"
  review: "Human Review"
  gate_approved: "Gate Approved"
  rework: "Rework"
  terminal: ["Done", "Closed", "Cancelled"]

polling:
  interval_ms: 15000

workspace:
  root: ~/code/stokowski-workspaces

hooks:
  after_create: |
    git clone --depth 1 git@github.com:your-org/your-repo.git .
  before_run: |
    git fetch origin main
    git rebase origin/main 2>/dev/null || git rebase --abort

claude:
  permission_mode: auto
  model: claude-sonnet-4-6
  max_turns: 20

agent:
  max_concurrent_agents: 4
  max_concurrent_agents_by_state:
    investigate: 2
    implement: 2
    code-review: 1                       # 串行 review 防 merge 冲突

prompts:
  global_prompt: prompts/global.example.md

server:
  port: 4200

states:
  investigate:
    type: agent
    prompt: prompts/investigate.md
    linear_state: active
    model: claude-opus-4-6
    max_turns: 8
    transitions:
      complete: research-review

  research-review:
    type: gate
    linear_state: review
    rework_to: investigate
    max_rework: 3
    transitions:
      approve: implement

  implement:
    type: agent
    prompt: prompts/implement.md
    linear_state: active
    model: claude-sonnet-4-6
    max_turns: 30
    transitions:
      complete: implementation-review

  implementation-review:
    type: gate
    linear_state: review
    rework_to: implement
    max_rework: 5
    transitions:
      approve: code-review

  code-review:
    type: agent
    prompt: prompts/review.md
    linear_state: active
    model: claude-opus-4-6
    runner: codex                         # 拿 GPT/Codex 第二意见（不同 provider）
    session: fresh                        # 对抗式：不继承前面 implement 的 session
    max_turns: 10
    transitions:
      complete: done

  done:
    type: terminal
```

## 状态机要点

| 字段 | 说明 |
|---|---|
| `type: agent` | Stokowski dispatch Claude Code 跑 prompt |
| `type: gate` | 暂停等人工 → Linear 上把状态改 `gate_approved` 触发 `approve`，或改 `rework` 触发 `rework_to` |
| `type: terminal` | issue 结束，清理 workspace |
| `transitions.complete` | agent 成功后跳到的下一个 state |
| `rework_to` | gate 被人工拒后回到的 state |
| `max_rework` | 最大返工次数（超过则进 terminal） |
| `session: inherit` | 沿用前一个 agent state 的 Claude session（保持 context） |

## Tracking 协议

Stokowski 在 Linear comment 里写 hidden 标记：

```html
<!-- stokowski:state {"state":"implement","run":1,"timestamp":"..."} -->
**[Stokowski]** Entering state: **implement** (run 1)
```

```html
<!-- stokowski:gate {"state":"research-review","action":"approve"} -->
**[Stokowski]** Gate approved → implement
```

人工**不要手动删这些标记** — 用 Linear 状态切换来控制 gate（改成 `Gate Approved` 或 `Rework`）。

## 常用模式

### 模式 1：纯调研（投石问路）

只跑 investigate state，结果发 Linear comment，人看完决定要不要继续。配置只留 `investigate` + 把 `transitions.complete` 指向 `done`。

### 模式 2：双 runner 第二意见

`code-review` state 配 `runner: codex` 而不是 Claude，用 GPT 模型做 adversarial review。

### 模式 3：并行多 issue

`max_concurrent_agents: 4` + `max_concurrent_agents_by_state: {implement: 2}` 让 4 个 issue 同时跑、其中 implement 阶段最多 2 个并行（防资源争抢）。

## 与 pi 工具链的关系

| 工具 | 适用场景 |
|---|---|
| **stokowski** | 长周期、多阶段、需要人工 gate 的项目工作（功能开发、调研报告） |
| **pi subagent worker** | 一次性子任务、不需要状态机（如"帮我写个脚本"） |
| **pi-coordination** | 多个独立 worker 并行（如"5 个 fact 同时写入"） |

## 排错

| 症状 | 排查 |
|---|---|
| `stokowski: command not found` | 没装；用 `python -m stokowski` 或先 `uv pip install -e .` |
| dry-run 无候选 issue | Linear `Todo` 状态名拼错；检查 `linear_states.todo` |
| agent 启动后秒退 | `claude` CLI 没装或 `permission_mode: auto` 被拒；先手工 `claude --version` |
| gate 不响应 | `linear_states.gate_approved` 名字和实际 Linear 状态名不一致 |
| 多 issue 抢同一 workspace | `workspace.root` 下每个 issue 自动建子目录，不会冲突；如冲突看 `hooks.after_create` 是否乱跑 |

## 参考

- README: `~/ghq/github.com/WeiYiAcc/stokowski/README.md`
- 完整 workflow: `~/ghq/github.com/WeiYiAcc/stokowski/workflow.example.yaml`
- prompts 模板: `~/ghq/github.com/WeiYiAcc/stokowski/prompts/`
- CLAUDE.md（项目内 LLM 注释）: `~/ghq/github.com/WeiYiAcc/stokowski/CLAUDE.md`
- 上游 Symphony spec: https://github.com/openai/symphony
Symphony spec: https://github.com/openai/symphony
