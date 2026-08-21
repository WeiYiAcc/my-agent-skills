---
name: my-multica
description: >
  Multica agent 平台的本机运维纪律 + Bub runtime 接入方案。
  涵盖：daemon 必须用 systemctl 管理（禁止 multica daemon start/restart）、
  掉线排查流程、bub-acp-server 接入（mcode 家族）、venv 补丁维护、
  skill 分发。触发场景：multica runtime 掉线/失联、daemon 操作、
  bub 接入 multica、agent skill 跨 runner 分发。
---

# Multica 本机运维

## daemon 管理纪律（最重要）

本机 daemon 由 home-manager 声明的 systemd user unit 托管
（source: `~/.local/share/chezmoi/home-manager/home_wsl.nix` 的 `multica` 段，
经 chezmoi apply 生效为 `~/.config/systemd/user/multica.service`）。

**一律用 systemctl，禁止 `multica daemon start/restart/stop`**：

```sh
systemctl --user status multica      # 看状态（真实 pid / 是否 active）
systemctl --user restart multica     # 重启（改了 config.json 或装了新 agent 后）
journalctl --user -u multica -f      # 日志；或 tail ~/.multica/daemon.log
```

原因：`multica daemon restart` 会杀掉 systemd 托管的进程并换成裸进程。
干净退出 exit 0 不会触发 `Restart=on-failure`，之后无人拉起 → 全部 runtime 失联。

service 已声明：代理（HTTPS_PROXY 经 VPS tailnet）、PATH 含 `~/.local/bin`
（所以 systemd 下不需要 path override）、`MULTICA_DAEMON_AUTO_UPDATE=false`
（版本由 nix/mise 固定，不会像手动 CLI 那样自己升级）。

## 掉线排查流程

1. `systemctl --user status multica` —— active 但 runtime 全 offline？看日志尾部
2. `tail ~/.multica/daemon.log` —— 正常退出会看到 `deregistered runtimes`；
   崩溃看 `~/.multica/daemon.err.log`
3. pid 文件可能残留死进程 pid，导致 `start` 报 "already running"：
   先 `multica daemon stop` 清态，再 `systemctl --user start multica`
4. 单个 runtime offline：`multica runtime list --output json` 看
   `runtime_profile_failure_reason`（多为 command not found → 检查 PATH 或 set-path）
5. 改 profile 后要 `systemctl --user restart multica` 重新探测

## Bub runtime 接入

- 插件安装（独立包有打包 bug，不要 `uv tool install bub-acp-server`）：
  `uv tool install bub --with bub-acp-server`
- Multica profile：display_name `Bub`，command `bub`，
  **protocol_family 必须用 `mcode`**（纯 ACP：initialize → session/new|load → prompt）
  - ❌ 不要用 `dim`：它强制发 `session/set_config_option permission=full-access`，
    bub 不认识该选项，失败即中止
- Agent 绑定后模型走 `~/.bub/config.yml`（openrouter:stealth/ox-alpha）

### venv 补丁（升级后会丢，需重打）

bub-acp-server 无条件把 `bash`/`fs.*` 工具替换成 ACP client 代理版，
而 Multica client 不支持这些能力 → 所有工具调用瞬间失败、模型死循环。
补丁：保留 builtin 本地工具。文件
`~/.local/share/uv/tools/bub/lib/python3.14/site-packages/bub_acp_server/agent.py`
中 `run_acp_agent` 内的 `with replace_builtin_tools(agent.client_tools):`
改为不启用（原文件备份 `agent.py.bak`）。改完用 ACP initialize 握手验证：

```sh
cd ~/hello-bub && printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize",
"params":{"protocolVersion":1,"clientCapabilities":{}}}' | timeout 20 bub acp | head -1
```

根治方案是给上游提 PR 加开关（replace_builtin_tools 加 config flag）。

## Skill 分发

Multica 自带 skill 管理（服务端分发到 runtime），当前未启用。
跨 runner 分发用社区 CLI，见 skill:my-agent-skills-distribution。
