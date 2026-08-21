---
name: rlm-delegate
description: >
  从 omp 委托任务给本机 prime-agent（RLM 架构，daemon 常驻）。触发场景：
  超长上下文分析（RLM 把 context 当变量递归分解）、需要后台长跑且终端可断开的任务、
  同一话题连续多轮快速追问（daemon 复用，4.9s/次）。也在用户说"用 prime-agent"、
  "后台跑个长任务"、"RLM"时触发。不适用：普通编码任务（omp 自己做）、
  需要 omp 工具链（skills/MCP/hub）的任务——prime-agent 是黑盒执行器，
  其内部子 agent 不进 omp 的 hub/IRC。
---

# rlm-delegate：omp → prime-agent 委托

## 一次性委托（同步，omp 等结果）

```bash
prime-agent -p --mode json "任务描述"          # 新 session
prime-agent -p -c --mode json "追问"            # 续最近 session（daemon 复用，~5s/次）
prime-agent -p -r <path|id> --mode json "..."   # 续指定 session（无 --session flag！那是 pi/omp 的）
```

结果解析：输出为 JSON 事件流，取最终答案：

```bash
... | jq -r 'select(.type=="agent_end") | .messages[-1].content[-1].text'
```

## 后台长跑（daemon-backed，终端可断）⚠️ 本节来自官方文档，未实测

（oneshot JSON 与 detach/attach 是 prime-agent 的两种不同执行模式；上一节的
oneshot 路径已 benchmark 验证，本节的 attach/goal/heartbeat 表面首次使用时
先小任务试跑，验证后删掉本警告行。）

```bash
prime-agent agents                    # 列出 running/idle/saved sessions
prime-agent attach <agent>            # 重新接上
prime-agent status / doctor           # daemon 健康
prime-agent shutdown --force          # 全部停掉（卡死时的重置手段）
```

长任务配 `/goal`（跨 turn 持续目标）、`/heartbeat`（定时自唤醒）、`/autonomous`（带预算的自主模式）。

## 实测性能（2026-08-06，i5-8265U WSL 2.9GB）

- 新 session 冷启动 7.5–14s；daemon 暖后续聊 **4.9s/次**
- daemon 常驻 ~230MB；空闲 worker ~30s 自动回收
- **并发禁忌**：冷 daemon 3 并发全灭（竞态）；暖 daemon 并发劣化 4 倍、峰值 1GB。
  串行使用；并发需求交给 multica（daemon 已限 max-concurrent-tasks=1）

## 模型接入

零配置——prime-agent 直接读 `~/.pi/agent/models.json`（axonhub 全系可用）。
指定模型：`--provider axonhub --model gpt-5.6-luna`。

## 边界与坑

- 工具级调用：omp 是指挥，prime-agent 是黑盒；通信靠 JSON 输出或文件，不进 omp hub
- `-p` 模式 stdin 必须可用；从脚本后台调用记得 `< /dev/null`，否则挂起
- 不支持 `--session <path>`（pi 协议 flag）；multica 集成走 `prime-agent-multica` shim
- 它的 skills 是 Python 包体系，和 pi/omp 的 md skills 不通用
