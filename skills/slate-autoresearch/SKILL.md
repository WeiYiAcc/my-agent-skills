---
name: slate-autoresearch
description: Drive slate's goal/autoresearch engine headlessly via slate-cli (no TUI needed). Use when asked to "run a slate goal", "run autoresearch via slate", "orchestrate subagents through slate", or when a task requires multi-step autonomous execution with rubric-based acceptance. Includes the .auto/ acceptance standard.
---

# Slate Autoresearch（headless goal 编排）

通过 `slate-cli`（纯 HTTP 薄客户端）驱动 slate 的持久化工作流引擎：
goal = planner 固化 requirements/rubric → worker/verifier 迭代 → gaps 回注自修复 → 全过即完成。

## 前置条件

- `slate-cli.ts` 位置：`~/ghq/github.com/WeiYiAcc/my-slate/cli/slate-cli.ts`（下称 `$SLCLI`）
- Bun ≥1.4（`mise use -g bun@1.4.0`）
- server 不在运行会自动拉起（cwd = `--dir`）；实例注册表在 `~/.slate-cli/instances.json`
- 工作区 `slate.json` 必须含 `"permission": {"*": "allow"}`，否则编排死循环烧 token：

```json
{ "$schema": "https://randomlabs.ai/config.json", "permission": { "*": "allow" } }
```

## 标准流程

```bash
SLCLI=~/ghq/github.com/WeiYiAcc/my-slate/cli/slate-cli.ts
DIR=/path/to/workspace   # goal 的所有文件操作都落在这里(server 按目录隔离实例)
mkdir -p "$DIR" && cd "$DIR"
[[ -f slate.json ]] || echo '{"$schema":"https://randomlabs.ai/config.json","permission":{"*":"allow"}}' > slate.json

# 启动(异步返回 [], 立即拿到 sessionID)
$SLCLI --dir "$DIR" goal "<objective>" --json > goal-run.json
SID=$(python3 -c "import json;print(json.load(open('goal-run.json'))['sessionID'])")

# 等待(--wait 版一步到位, 轮询至 completed 或超时)
$SLCLI --dir "$DIR" goal "<objective>" --wait --timeout 1800 --json > goal-run.json
```

## 监控与诊断

```bash
$SLCLI workflow list --session "$SID"          # run 列表(completed/failed)
$SLCLI workflow graph <runID>                  # program 图
$SLCLI events watch --types message.updated,workflow_run.updated   # 实时事件(SSE)
$SLCLI session messages "$SID"                 # 最终 assistant 消息含 "Goal complete ✅"
$SLCLI perm list                               # headless 下权限请求会堆积在这里, 用 reply 处理
$SLCLI perm reply <requestID> always           # 批准(once/always/reject)
```

## ⚠️ 已知行为（必读）

1. **文件操作落在 server cwd**：同目录复用实例（注册表去重），跨目录自动新开端口。
   不要在一个 server 目录里跑另一个目录的 goal。
2. **异步语义**：`session command` 立即返回 `[]`；完成判定只看
   `workflow-run status` 或最终 assistant 消息的 "Goal complete ✅"。
3. **模型劣化期**：上游偶发空白响应/畸形 tool args → run failed。
   处置 = 直接重跑同一 goal（原版 TUI 同样如此）；连续 2 次 failed 应检查
   `/tmp/kms/mirror.log` 与 pong 探测（见 my-gproxy/docs/slate-decoupling-stack.md）。
4. **测试工作区不要留日志/杂文件**——goal 子代理会去读它们然后把自己搞 blocked。
5. `workflow-run` 必须带 sessionID 参数。

## /autoresearch 验收标准

一个 run 要被判定为「符合 autoresearch 标准」，必须同时满足：

1. **交付物存在且内容精确匹配** objective 的显式要求
2. **`.auto/measure.sh` 存在且可执行**，输出至少一行 `METRIC <name>=<value>`
3. **`.auto/log.jsonl` 有记录**：每次尝试一条 JSON 行
   （`{"iteration":n,"idea":"...","metric":...,"decision":"keep|discard|crash|checks_failed"}`）
4. **`.auto/checks.sh` 通过**（若 objective 定义了正确性检查）
5. 最终状态 completed 且无未处理 permission 挂起

需要数值优化类任务时，在 objective 里显式要求 agent 按 pi-autoresearch 的
`.auto/` 布局组织实验循环（prompt.md/measure.sh/log.jsonl），goal 引擎会把它当
rubric 逐条验证。

## 故障排查

| 症状 | 处置 |
|---|---|
| goal failed, tool_response 里 TOOL_VALIDATION_ERROR | 模型畸形输出，重跑 |
| orchestration 死循环 | 检查 slate.json 是否有 permission allow-all |
| 卡在 permission | `$SLCLI perm list` + reply |
| 连续空白响应 | 上游劣化期，等窗口或换供给（见解耦文档） |
