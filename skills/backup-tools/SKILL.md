---
name: backup-tools
description: >
  Linux 备份与同步工具的深度参考 — restic、rclone、rsync。涵盖配置、命令速查、
  常见错误、坑点。当用户讨论备份策略、加密备份、云存储同步、文件镜像、OneDrive/S3
  同步、snapshot/restore、rclone 远端配置、rsync --delete、restic 密码管理、forget+prune
  等任何涉及这三个工具的话题时使用。
---

# Backup Tools Reference

三个工具各有定位：

| 工具 | 核心能力 | 最佳场景 |
|---|---|---|
| **restic** | 内容寻址的加密去重备份库 | 长期历史 + 本地/云存储 + 需要加密 |
| **rclone** | 70+ 云存储后端的同步/挂载 | 把本地目录 sync 到 OneDrive/S3/Google Drive 等 |
| **rsync** | 文件级增量同步 | 本地/SSH 目录镜像、快速一次性同步 |

> 知识来自 [L3DigitalNet/Claude-Code-Plugins](https://github.com/L3DigitalNet/Claude-Code-Plugins)
> 的 linux-sysadmin plugin（已 fork 到 WeiYiAcc/Claude-Code-Plugins），
> 以 MIT License 使用。每个 guide 都有 identity / quick start / key operations /
> health checks / common failures / **pain points** 等系统化 section。

## 触发场景

当用户说以下任何一类时，**读对应的 guide**：

### restic 触发词
"restic"、"加密备份"、"去重备份"、"snapshot"、"forget"、"prune"、
"restore"、"check repository"、"初始化仓库"、"密码文件"

→ 读 `references/restic/guide.md`
→ 需要部署场景（local / SFTP / S3 / B2 / REST）时读 `references/restic/references/common-patterns.md`
→ 需要命令速查时读 `references/restic/references/cheatsheet.md`

### rclone 触发词
"rclone"、"OneDrive 同步"、"S3 同步"、"云存储同步"、"rclone config"、
"rclone copy"、"rclone sync"、"rclone mount"、"rclone 远端"、"rclone bisync"

→ 读 `references/rclone/guide.md`
→ 命令速查：`references/rclone/references/cheatsheet.md`

### rsync 触发词
"rsync"、"增量同步"、"rsync --delete"、"rsync -av"、"archive mode"、
"SSH 同步"、"目录镜像"、"dry-run sync"、"itemize-changes"

→ 读 `references/rsync/guide.md`
→ 命令速查：`references/rsync/references/cheatsheet.md`

## 重要 pain points 摘要（AI 自己先记住）

### restic
1. **`forget` 和 `prune` 是分开的** — `forget` 只标记，不释放磁盘；用 `forget --prune` 或后续 `prune`
2. **没密码完全无法恢复** — AES-256 + PBKDF2，密码丢了数据就丢了
3. **`check` vs `check --read-data`** — 前者快（只验 metadata），后者慢（验所有 blob hash）
4. **snapshot ID 不稳定** — 短 ID 会碰撞，脚本用 `latest` 或完整 64 字符
5. **lock file deadlock** — 两个并发 `backup` 会死锁，cron/systemd 用 `Conflicts=` 或 `flock`
6. **默认会备份 cache** — 加 `--exclude-caches` + 显式 `--exclude` 排除 `node_modules`/`.venv` 等

### rclone
- `copy` 不删除，`sync` 会删除目标端多余文件
- **永远先 `--dry-run`** 尤其 `sync` 操作
- `lsf`（简单）/ `ls`（详细）/ `lsjson`（结构化）
- `rclone config` 是交互式向导
- WSL 里配 headless（无浏览器）用 `rclone authorize` 从另一台机器拿 token

### rsync
- **永远先 `-avn`（dry-run）** 尤其是 `--delete` 前
- `-a` = `-rlptgoD` 归档模式（preserve perms/times/symlinks/owner/group）
- `--itemize-changes` 看具体改了什么、为什么
- `-h --progress` 人类可读进度
- 目录末尾斜杠有语义差异：`/src/` → 复制内容，`/src` → 复制目录本身

## 目录结构

```
backup-tools/
├── SKILL.md                             ← 本文件（dispatcher）
└── references/
    ├── restic/
    │   ├── guide.md                     ← restic 主 guide
    │   └── references/
    │       ├── cheatsheet.md            ← 按任务组织的命令速查
    │       ├── common-patterns.md       ← local/SFTP/S3/B2 等完整部署场景
    │       └── docs.md                  ← 官方文档链接
    ├── rclone/
    │   ├── guide.md
    │   └── references/
    │       ├── cheatsheet.md
    │       └── docs.md
    └── rsync/
        ├── guide.md
        └── references/
            ├── cheatsheet.md
            └── docs.md
```

## 使用原则

- **遇到这三个工具的具体问题** → 先读对应 `guide.md` 的 pain points 部分，90% 的坑在那里
- **要写脚本做备份** → 看 `common-patterns.md`（目前只有 restic 有），里面是完整可用的 shell 片段
- **找命令** → `cheatsheet.md` 按任务分类
- **追踪最新上游变化** → 用户可以 `cd ~/.pi/agent/skills/backup-tools/references && <sync 脚本>` 从 fork 拉更新

## 交叉引用

- fact `backup-tools-linux-sysadmin-plugin` — 这个 skill 的来源与设计记录
- fact `sillytavern-git-hook-restic-sync` — restic 实战案例（git hook 触发同步）
- `~/my-SillyTavern/tools/polylith/` — restic-backup polylith 实现，实际的生产代码
