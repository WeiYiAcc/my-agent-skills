---
name: multica-cli
description: >-
  multica CLI 调用速查。issue/agent/runtime/daemon/skill 等子命令的参数、JSON
  输出结构、分页与 UUID 坑。当需要查 multica 任务结果、读 issue 评论、操作
  runtime/daemon、或用户提到 multica 平台数据（issue、评论、内存基准、对比测试）
  时使用。
---

# multica CLI 速查

## 核心命令地图

```
multica issue list|get|create|comment|children|metadata|assign|cancel-task|label|property
multica agent / runtime / squad / project / repo / chat / skill / workspace / autopilot
multica daemon status|start|stop|restart|logs|disk-usage
multica config / auth / login / setup / update / user
```

## 高频调用模式

```bash
# 分页拉 issue（JSON 里 id 是 UUID，没有 WEI key！）
multica issue list --limit 100 --offset 0 --output json

# 按 UUID 取详情 / 评论（WEI-xxx key 不能用于 get/comment）
multica issue get <uuid> --output json
multica issue comment list <uuid> --output json
multica issue comment add <uuid> --content "..."

# daemon
multica daemon status   # 注意：孤儿进程占端口时 status 仍报 running（假在线）
multica daemon logs --head | tail
```

## JSON 结构坑

- `issue list` 返回 `{"issues": [...]}` 或裸数组（版本而异）；`status`/`assignee`
  是**对象**（取 `.name`），`id` 是 UUID，**没有 key 字段**——WEI 编号只在 table 输出里。
- issue 的实际产出（测试结果、benchmark 数据）在**评论里**，`issue get` 的
  description 只有任务描述。查结果必须 `comment list`。
- gate-squad 的审批评论带 `<!-- gate-squad:state {...} -->` 标记，按 content 过滤。
- 数据量大（400+ issue）时用 `--limit 100 --offset N` 循环翻页。

## 关键事实（2026-08-22）

- workspace 共 438+ issue；benchmark 类 issue 标题含「内存基准-*」「执行对比」
  「内存占用排名」，结果在评论。
- runtime profile 命令解析经 `~/.multica/config.json` 的
  `profile_command_overrides`（chezmoi 模板管理，勿手动 set-path），
  改后需 `multica daemon restart`。
- agent→runtime 绑定等 server 侧配置的版本化锚点：`~/.multica/AGENTS_CONFIG.md`
  （改配置后当次会话必须更新它并 jj 提交）。
- daemon 是 systemd 用户服务 `multica.service`；端口 19514。
- benchmark 权威数据：fact `multica-runtime-selection-2026-08`（冷启动/内存/并发）、
  issue `fa7be8bc`（WEI-489 七 runtime token/耗时对比表）。
