---
name: my-clash-config
description: >
  mihomo/clash 配置的修改纪律与工作流。配置唯一真相源是 GitHub gist
  （my_mihomo_multi.yaml），所有改动必须 PATCH gist 后再分发，禁止直写本机
  运行时配置文件。覆盖：FlClash/WSL 双实例关系、tailnet 排除段、保护性
  DIRECT 规则、验证方法（TCP 握手假接受陷阱）。
---

# my-clash-config — mihomo 配置经 gist 管理的工作流

## 铁律

**禁止直接编辑本机任何 clash/mihomo 运行时配置文件**：

- `AppData/Roaming/com.follow/clash/config.yaml`（FlClash 生成物，会被重生覆盖）
- `com.follow/clash/profiles/*.yaml`（GUI 订阅源，刷新即丢）
- `AppData/Roaming/com.follow/clash/config.json`（覆写文件，字段可能被规范化剥离）

**唯一写入口 = gist**。改完 PATCH 上去，再分发/重载。

## 架构（2026-08-23 实测拓扑）

```
gist: my_mihomo_multi.yaml (WeiYiAcc/81a11b4dd9f28413d4856379c035dc9e)
  ↓ pull / 手动部署
Windows mihomo 实例 (mixed-port 7897, TUN strict-route)
  ↑ TUN 抓获全机流量（含 WSL NAT 出站）
fedora WSL (env proxy → 127.0.0.1:7890 → FlClash 或节点链路)

旁路实例：
- FlClash (mixed-port 7890)：日常给 WSL 供代理的 GUI 实例
- WSL 本地 mihomo (/tmp/kms/mihomo-dns.yaml)：仅 slate DNS 层，非代理
```

注意：7897(gist) 与 7890(FlClash) 是**两个不同实例**，配置互不相通。
临时切端口前先确认目标实例的规则集包含你依赖的规则。

## 标准工作流

### 1. 读当前配置

```bash
curl -sS "https://gist.githubusercontent.com/WeiYiAcc/81a11b4dd9f28413d4856379c035dc9e/raw/my_mihomo_multi.yaml" -o /tmp/current.yaml
```

### 2. 修改并 PATCH 回 gist

```bash
uv run --no-project - <<'EOF'
import json
s = open('/tmp/current.yaml').read()
# ... 修改 ...
new = s.replace(OLD, NEW, 1)
open('/tmp/new.yaml','w').write(new)
payload = {"files": {"my_mihomo_multi.yaml": {"content": new}}}
json.dump(payload, open('/tmp/gist_patch.json','w'))
EOF
gh api -X PATCH gists/81a11b4dd9f28413d4856379c035dc9e --input /tmp/gist_patch.json -q ".updated_at"
```

### 3. 验证（raw 无 hash 有 CDN 缓存，必须用版本化 URL）

PATCH 返回的 `.files["..."].raw_url` 自带 commit hash，用它回读确认。

### 4. 分发生效

- Windows 实例：重新下载/拉取该配置后重载（GUI 操作）
- 其他机器：同 URL 可直接拉

## 已固化在 gist 里的关键规则（勿删）

```yaml
rules:
  - IP-CIDR,100.64.0.0/10,DIRECT,no-resolve        # tailnet CGNAT 段直连（第一条！）
  - IP-CIDR,104.168.22.124/32,DIRECT,no-resolve    # racknerd 公网：保护 tailscale WG UDP 不进节点
tun:
  route-exclude-address:
    - 100.64.0.0/10                                 # tailnet 不进 TUN 路由
    - 100.110.98.84/32                              # racknerd 本机双保险
```

背景：strict-route 会把 tailscale 的 WireGuard UDP 也抓进 TUN 按 MATCH 兜底走节点，
节点抖动 = 整条 tailnet 链路（gost 出口、SSH、cli-proxy-api）一起断。这两组规则解耦之。

## 排障纪律

1. **TCP 握手成功 ≠ 可达**。gvisor TUN 会假接受任意端口的 SYN 再失败，
   必须发真实数据请求看 HTTP code 与 body。
2. **端口扫描结果不可信**，同因。
3. 改规则后怀疑未生效：对比「运行时生成配置」与 gist 内容——
   FlClash 场景下生成物在 `com.follow/clash/config.yaml`，只读诊断可以，
   但修复永远落在 gist。
4. 节点不稳时段（RST/超时成簇出现）：先区分「路径问题」还是「节点问题」——
   用 `tailscale nc`（tailscaled 内部管道，不过 TUN 规则处理）做对照测试。
