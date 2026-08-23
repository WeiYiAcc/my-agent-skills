---
name: my-agent-skills-distribution
description: >
  Agent skill 跨 runner 分发方案选型与操作。从一个 git 仓库把 skills
  分发到各 coding agent 的全局位置（~/.claude/skills、~/.pi/agent/skills 等），
  同时支持项目级管理。触发场景：新增/同步 skill 到多个 agent、
  skill 版本漂移、上游更新推送。
---

# Agent Skills 跨 runner 分发

## 选型结论（2026-08）

| 工具 | 定位 | 适用 |
|---|---|---|
| **vercel-labs/skills**（`npx skills`） | 事实标准，skills.sh 生态，73+ agents | 首选：从 GitHub 装 skill 到全局 `-g` 或项目级，带 lock file 和 `skills update` |
| **jgordijn/agentdeps** | 声明式 `agents.yaml`，git 依赖 | 想要「一个 yaml 描述所有 runner + 仓库」的声明式流；明确支持 Pi |
| **helincao/skilled** | 带 upstream 回推 | 本地改了 skill 还要 push 回仓库的场景 |
| Multica 内置 skill 管理 | 服务端分发到 runtime | 已决定不启用 |

## 推荐组合

自建 skill 仓库（如 `WeiYiAcc/agent-skills`，标准 agentskills.io 格式：
每个 skill 一个目录含 SKILL.md），然后：

```sh
# 全局安装（各 runner 的全局 skills 目录）
npx skills add WeiYiAcc/agent-skills --skill my-multica -g

# 项目级安装（装进项目目录，随仓库走）
cd some-project && npx skills add WeiYiAcc/agent-skills --skill code-style

# 全部更新
npx skills update
```

原则：**单一 source of truth = git 仓库；各 runner 目录只是分发产物**，
不要手改产物（和 chezmoi 的 source/target 纪律同构）。

## 与现有体系的关系

- `~/.pi/agent/skills/` 里已有大量手动维护的 skill——迁移时以仓库为准，
  把本地当初始版本 push 上去，再改为分发安装
- chezmoi 只管「必须每台机器都在」的基础设施类文件；skill 更新频繁，
  走 skills CLI 的 lock/update 流程更合适，不要塞进 chezmoi

## 动态更新：symlink 是默认

`npx skills` 默认安装方式就是 **symlink**（各 agent 目录 → canonical 副本，
`--copy` 才是复制）。更新两条路：

1. 直接改 canonical 副本 → 所有 runner 即时生效（symlink 实时可见）
2. 改 git 仓库 → `npx skills update [name]`（增量 re-add，symlink 不动）

工作流与 chezmoi source/target 纪律同构：git 仓库 = source，
canonical 副本与各 runner 目录 = 分发产物，永不手改 target。
Pi 在支持列表（`-a pi`，全局路径 `~/.pi/agent/skills/`）。

## 故障排查纪律（2026-08-23 补充）

发现 `~/.pi/agent/skills/`（或任何 runner 目录）下出现**非符号链接的真实目录**时：

1. 先假定分发流程被绕过（某个 agent / 工具直写了产物区），不要直接当独立 skill 处理
2. 与 `~/.agents/skills/` canonical 副本 diff：一致 → 删真实目录改回 symlink；
   不一致 → 先回溯差异来源（哪次写入、什么工具），确认内容归属后再决定收编进仓库还是删除
3. 修复后回查是谁绕过了流程（文件 mtime、会话记录），堵住源头
4. pi 会同时扫描 `~/.pi/agent/skills/` 和 `~/.agents/skills/` 两个用户级目录并按真实路径去重——
   同名真实目录 + canonical 副本并存会报 skill collision 警告（案例：my-clash-config，2026-08-23）
