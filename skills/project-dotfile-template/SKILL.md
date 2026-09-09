---
description: 项目级别 dotfile 模板分发方案（替代 chezmoi .tmpl + HM 模板）
version: 1.0
tags: [dotfile, sops, secretspec, mr, jj, template, project-level]
---

# 项目级别 dotfile 模板方案

替代 chezmoi `.tmpl` + home-manager `home.file` 模板的统一方案。适用于多主机（WSL/VPS/desktop）、多仓库（prime/atomic/omp/dirge/dot-pi-config）。

## 核心规则

- **单仓库 = 单一真相源**：每个 `.xxx-multica-agent/agent/` 或 `dot-pi-config/` 是独立 `jj` 仓库，由 `mr` 编排。
- **不再使用 `.tmpl`**：模板变量（`{{ .chezmoi.hostname }}`、`joinPath`）直接写死或运行时检测，编译时渲染由 `jj` + `sops` 完成。
- **密钥管理**：每仓库独立 `secretspec.toml` + `.enc.yaml`（sops + age），`.jjignore` 过滤 `.env` / `.enc.yaml`。
- **最小 `.sops.yaml`**：每仓库只含自身 `age` 公钥（`age10ue93j9...`），不含全量密钥。

## 目录结构

```
repo/
  .sops.yaml              # 最小 age 规则（仅本仓库公钥）
  secretspec.toml         # profile + secret 声明（provider = sops）
  .jjignore               # .env / .env.enc.yaml / .enc.yaml / transient/
  config.json.trimmed     # 无密钥的配置源
  openrouter.enc.yaml     # sops 加密（对应 secret 名称）
  .env                    # 本地明文（被 .jjignore 过滤，系统访问受控，不进远端）
```

## 密钥拆分映射（从 chezmoi secrets.yaml 派生）

| 仓库 | .enc.yaml 内容 | secretspec 声明 |
|---|---|---|
| `multica-runners-prime-agent` | `llm_proxy.enc.yaml`（OMNIROUTE/GPT_LOAD/SUB2API...） | 8 个 secret |
| `multica-runners-atomic` | 无（或 `openrouter.enc.yaml` 如需要） | 无 / 最小 |
| `multica-runners-omp` | `llm_proxy.enc.yaml`（SUB2API_OPENCODE/NEWAPI/GPROXY/ZEN） | 4 个 secret |
| `multica-runners-dirge` | `openrouter.enc.yaml` | 1 个 secret |
| `dot-pi-config` | 根据 `secrets.yaml` 拆分（LLM proxy + search + ai_memory） | 对应声明 |

## 主机差异处理（替代 `.chezmoi.hostname`）

- **方案 A（推荐）**：`jj` 分支。`main`（共用）+ `wsl`（WSL 特有）/ `racknerd-f76a666`（VPS 特有）。
- **方案 B（运行时）**：`.envrc`（direnv）检测 `HOSTNAME`，设置 `DIRGE_HOST=wsl/vps`，调整 `PATH` / `OPENROUTER_API_KEY_FILE` 路径。
- **方案 C（nix 编译时）**：`home-manager` 分支 `weiyiacc@wsl` / `weiyiacc@racknerd-f76a666`，不同 `modules/*.nix` 声明不同内容。

不使用 `.tmpl` 变量：

```yaml
# 旧：dot_pi/agent/settings.json.tmpl
{{- $target := joinPath .chezmoi.homeDir ".atomic/agent/settings.json" -}}

# 新：直接写死或运行时检测
# dot-pi-config/.pi/agent/settings.json（纯文件）
{
  "defaultProvider": "gproxy",
  "defaultModel": "ox-alpha-free"
}
```

## 操作流程

1. `jj git init --colocate` 初始化仓库
2. 创建 `.sops.yaml`（最小 age 规则）
3. `secretspec.toml` 声明 secret
4. `sops --encrypt` 生成 `.enc.yaml`
5. `jj add` 加入（`.env` 不加入，`.jjignore` 过滤）
6. `jj describe -m "feat: add sops..."`
7. `jj git push --bookmark main --remote origin`

## 验证步骤

```bash
# secretspec 检查
secretspec check -f secretspec.toml

# sops 解密检查
sops -d openrouter.enc.yaml  # 仅在有 age 私钥的主机执行

# 远端无泄露
curl -s https://api.github.com/repos/WeiYiAcc/multica-runners-dirge/contents/ | grep .env || echo "无 .env"
```

## 依赖

- `jj`（VCS，colocate 默认）
- `mr`（多仓库管理，`vcs = jj`）
- `secretspec` 0.14（TOML 配置 + sops provider）
- `sops` 3.13.1 + `age`（加密）
- `direnv`（可选，目录级环境加载）
- `mise`（可选，工具版本管理，独立于 HM）

## 相关文件路径（本环境已验证）

- `~/ghq/github.com/WeiYiAcc/home-manager/modules/mr.nix`
- `~/.dirge-multica-agent/agent/secretspec.toml`
- `~/.dirge-multica-agent/agent/openrouter.enc.yaml`
- `~/.dirge-multica-agent/agent/.sops.yaml`
- `~/.config/secretspec/config.toml`（provider = sops）
- `~/.local/state/nix/profiles/home-manager/home-path/bin/secretspec`
- `~/.local/share/chezmoi/.sops.yaml`（源规则，已拆分为各仓库独立版本）
