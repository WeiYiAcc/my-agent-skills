---
name: nix-home-manager
description: 管理 Nix Home Manager 配置的标准操作流程。覆盖 WSL 本机和 RackNerd 服务器。安装/卸载包、home-manager switch、chezmoi push。禁止使用 nix-env -iA 安装包（会和 home-manager profile 冲突导致 OOM）。
---

# Nix + Home Manager Skill

## ⚠️ 铁律：禁止 `nix-env -iA`

**所有包只通过 home-manager 管理，绝对不要用 `nix-env -iA` 安装包。**
`nix-env` 和 `home-manager` 共享同一个 `~/.nix-profile`，混用会导致 eval 时内存暴涨（1.9G VPS 直接 OOM）。

## 多机配置

| 机器 | 配置文件 | Flake target | 执行方式 |
|---|---|---|---|
| WSL 本机 | `~/home-manager/home_wsl.nix` | `weiyiacc@wsl` | 直接执行 |
| RackNerd 服务器 | `~/home-manager/home_racknerd-f76a666.nix` | `weiyiacc@racknerd-f76a666` | SSH 远程执行 |

两个配置文件都由 chezmoi 管理（`~/.local/share/chezmoi/home-manager/`）。

## 标准流程（本机 WSL）

```bash
# 1. dry-run：只构建，不切换（验证配置无误）
home-manager build --flake "$HOME/home-manager#weiyiacc@wsl"

# 2. 确认无误后 switch（带时间戳备份）
home-manager switch -b "backup_$(date +'%Y-%m-%dT%H_%M_%S')" --flake "$HOME/home-manager#weiyiacc@wsl"
```

> **必须先 build**。build 失败则不执行 switch，避免 profile 半损。
> 命令用 `$HOME/home-manager` 绝对路径，不依赖 cwd。

## 服务器流程（RackNerd）

```bash
# 1. 本机编辑配置
nvim ~/.local/share/chezmoi/home-manager/home_racknerd-f76a666.nix

# 2. 同步到服务器
ssh -p 48722 weiyiacc@104.168.22.124 "cat > ~/home-manager/home_racknerd-f76a666.nix" \
  < ~/.local/share/chezmoi/home-manager/home_racknerd-f76a666.nix

# 3. 服务器上执行（限制资源，1.9G VPS 容易 OOM）
ssh -p 48722 weiyiacc@104.168.22.124 'export PATH=$HOME/.nix-profile/bin:$PATH && \
  home-manager switch -b "backup_$(date +%Y-%m-%dT%H.%M.%S)" \
  --flake ~/home-manager#weiyiacc@racknerd-f76a666 --max-jobs 1 --cores 1'

# 4. 验证
ssh -p 48722 weiyiacc@104.168.22.124 "export PATH=\$HOME/.nix-profile/bin:\$PATH && which <cmd>"
```

### 服务器 OOM 应急

如果 SSH 断连（nix eval 内存不足）：
1. 等 2-5 分钟服务器自动恢复
2. 先停 Docker 释放内存：`docker stop sub2api sub2api-postgres sub2api-redis newapi omniroute open-webui`
3. 重试 home-manager switch
4. 成功后恢复 Docker：`docker start omniroute newapi open-webui sub2api-postgres sub2api-redis sub2api`

## 完整流程（添加包）

1. 编辑对应的 `home_*.nix`，在 `home.packages` 里加 `pkgs.<name>`
2. 验证包名存在：`nix-instantiate --eval -E 'builtins.hasAttr "<name>" (import <nixpkgs> {})'`
3. dry-run build（本机）或直接 switch（服务器）
4. switch（带备份）
5. 验证安装：`which <cmd> && <cmd> --version`
6. 修改的是 chezmoi source（`~/.local/share/chezmoi/home-manager/`）还是 target（`~/home-manager/`）：
   - **改 source 后**：`chezmoi apply ~/home-manager/home_wsl.nix` 让 target 生效，再 switch
   - **改 target 后**（如程序改动）：`chezmoi add ~/home-manager/home_wsl.nix` 同步回 source
7. chezmoi 提交推送（**jj 流程**）：
```bash
cd ~/.local/share/chezmoi
jj commit -m "chore(home-manager): add <pkg>"
jj git push
```

## systemd user unit 管理

home-manager 可声明 `systemd.user.services` / `systemd.user.timers`：

```nix
# 示例：定时备份 timer
systemd.user.services.restic-backup-runtime = {
  Unit.Description = "Restic backup";
  Service = {
    Type = "oneshot";
    ExecStart = "%h/.local/bin/restic-backup-runtime.sh";
  };
};
systemd.user.timers.restic-backup-runtime = {
  Unit.Description = "Backup every 30 min";
  Timer = { OnBootSec = "5min"; OnUnitActiveSec = "30min"; };
  Install.WantedBy = [ "timers.target" ];
};
```

- systemd 是 PID 1 时：`home-manager switch` 自动 enable + 启动
- systemd 不可用时（WSL 未配置）：unit 文件生成但不激活，需要 login shell fallback 兜底
- `/etc/wsl.conf` 是系统级配置，**不由 chezmoi/home-manager 管理**

## 非 systemd 环境 fallback

在 `programs.bash.profileExtra` 里用后台 loop 兜底（纯 user 空间，login 时触发）：

```nix
profileExtra = ''
  # systemd 不可用时，后台 loop 代替 timer
  if [ "$(cat /proc/1/comm 2>/dev/null)" != "systemd" ]; then
    _pidfile="/tmp/.restic-backup-loop.pid"
    if [ -f "$HOME/.local/bin/restic-backup-runtime.sh" ] \
       && ! (kill -0 "$(cat "$_pidfile" 2>/dev/null)" 2>/dev/null); then
      ( while true; do
          "$HOME/.local/bin/restic-backup-runtime.sh" >> /tmp/pi-backup.log 2>&1 || true
          sleep 1800
        done ) &
      echo $! > "$_pidfile"
    fi
  fi
'';
```

## 查包名
```bash
# 精确匹配
nix-instantiate --eval -E 'builtins.hasAttr "<name>" (import <nixpkgs> {})'
# 模糊（慢，避免用）
nix-env -qaP '<name>'
```

## 注意事项
- **switch 后必须提交 chezmoi**（jj commit + push，见上文第7步），保持远端同步
- `-b` 备份参数防止 switch 失败时文件冲突
- chezmoi source dir 用 jj 管理（已 jj colocate，WEI-399）
- `home.packages` 里加包，不要用 `programs.<name>` 模块（除非需要声明配置）
- jeezyvim 通过 overlay 注入，不在普通 packages 列表里
- **不要用 chezmoi run_after 管理需要 root 的系统配置**（如 `/etc/wsl.conf`）
- **新版 home-manager fzf+atuin 抢 Ctrl-R 冲突**：升级 nixpkgs/home-manager 大版本后，build 会警告 fzf 和 atuin 都想绑 Ctrl-R。已按社区主流方案解决——atuin 拥有 Ctrl-R（历史搜索，跨机同步+上下文），fzf 让出、保留 Ctrl-T（文件查找）和 Alt-C（目录跳转）。配置：`programs.fzf.historyWidget.command = ""`（home_wsl.nix）。若再报此警告说明配置被覆盖，检查这行。
- **nix 大版本升级同步**：另一台机器改了 flake.nix 的 nixpkgs pin 后，本机 chezmoi pull → `chezmoi apply` → `home-manager build`（验证）→ 若 build 产物 = 当前 generation 说明已跟上、无需 switch，否则 switch。用 `nix flake metadata --json` 看 root.inputs.nixpkgs 的真实 rev（flake.lock 里有多个 nixpkgs node，grep 会看错）。

## 当前已安装关键包

### home_wsl.nix（本机）
| 分类 | 包名 |
|---|---|
| jj 生态 | `jujutsu`, `jjui` |
| diff | `difftastic`（delta 已于 2026-07 移除） |
| secret | `sops` |
| dotfiles | `chezmoi` |
| 运行时 | `nodejs_22`, `pnpm`, `bun`, `go`, `uv`, `clojure`, `babashka` |
| 编辑器 | `jeezyvim`(overlay), `emacs30` |
| CLI | `gh`, `lazygit`, `ripgrep`, `fd`, `aichat`, `go-task`, `atuin` |

### home_racknerd-f76a666.nix（服务器）
| 分类 | 包名 |
|---|---|
| 基础 | `gzip`, `gnutar`, `direnv`, `wget`, `curl`, `unzip` |
| 编辑器 | `jeezyvim`, `hunspell`, `discount` |
| CLI | `ripgrep`, `fd`, `jet`, `nushell`, `go-task`, `yt-dlp` |
| 服务 | `syncthing`, `caddy`, `dnscontrol` |
| 加密 | `sops`, `age`, `chezmoi` |
| 网络调试 | `ngrep`, `tcpdump` |
