---
name: multica-local-notes
description: >-
  multica 本机环境补充：JSON 结构坑、评论承载结果、benchmark 数据索引、daemon
  假在线陷阱。配合官方 multica-cli skill 使用——命令参数以官方 skill 为准，本
  skill 只记 WeiYiAcc 环境特有事实。当需要查 multica 任务结果、benchmark 数据
  （内存基准/执行对比/冷启动实测）、或排查 multica daemon 异常时使用。
---

# multica 本机环境补充

> **前置**：命令参考先读官方 `multica-cli` skill（multica-ai/multica-cli，要求
> CLI ≥ 0.4.26）。本 skill 不重复命令面，只记本机特有事实与数据索引。

## JSON 结构坑

- `issue list` 返回 `{"issues": [...]}` 或裸数组（版本而异）；`status`/`assignee`
  是**对象**（取 `.name`），`id` 是 UUID，**没有 key 字段**——WEI 编号只在 table 输出里。
- issue 的实际产出（测试结果、benchmark 数据）在**评论里**，`issue get` 的
  description 只有任务描述。查结果必须 `comment list`。
- 数据量大（438+ issue）时用 `--limit 100 --offset N` 循环翻页。

## 搜索能力限制（2026-08-22 实测，v0.4.32）

- `issue search` 不索引**评论内容**；中文标题命中差（搜「内存基准」0 命中）；
  多词查询报错。找历史数据靠英文关键词碰运气 + 分页遍历 + 标题过滤。
- 快路径：先查 fact `multica-cli-cheatsheet` 的数据索引，直达 issue UUID。

## 本机环境

- daemon = systemd 用户服务 `multica.service`（端口 19514）。
  **孤儿进程占端口时 `daemon status` 假报 running**（2026-08-22 事故，
  restart counter 769）——status 可疑时 `systemctl --user status multica` 对账。
- runtime profile 命令经 `~/.multica/config.json` 的 `profile_command_overrides`
  固定（chezmoi 模板管理，勿手动 set-path），改后需 `multica daemon restart`。
- agent→runtime 绑定等 server 配置的版本化锚点：`~/.multica/AGENTS_CONFIG.md`
  （改配置后当次会话必须更新它并 jj 提交）。
- omp 不在 skills CLI 支持列表，官方 skill 需手动拷到 `~/.omp/agent/skills/multica-cli/`。

## benchmark 数据索引

| 数据 | 位置 |
|---|---|
| 冷启动/内存/并发（笔记本+VPS 两台机器完整版） | fact `multica-runtime-selection-2026-08` |
| WEI-489 七 runtime token/耗时对比原始记录 | issue `fa7be8bc` 评论 |
| Prime vs Atomic RSS 实测（prime 内存大户但最快） | issue `fa7be8bc` 评论 |
| 台式机空闲采样（pi 234.6MB / atomic 199.7MB） | issue `ab189fbe` 评论 |

## 更新纪律

- 官方 skill 更新：`npx skills update`（pi/claude-code 走 symlink 自动生效）；
  omp 侧手动重新拷贝 `skills/multica-cli/SKILL.md`，**不要**把本文件内容并进去。
