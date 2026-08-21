---
name: docker-network-debug
description: Docker 容器 + 反向代理（Caddy/Nginx）网络问题排查方法论。涵盖：容器无法被外网访问、客户端报 download/fetch failed、反代配置错误、BASE_URL/EXTERNAL_URL 配错、TLS 握手超时、大文件传输中断。当 Docker 服务对外暴露出现连接问题时使用。
---

# Docker + 反向代理网络排查 Skill

## 核心原则

**先抓包，再猜测。** 90% 的"网络问题"实际是配置问题，抓到实际 HTTP 请求/响应就能定位。

## 排查顺序（必须按此顺序）

### 1. 确认服务本身存活

```bash
# 从 VPS 本机测试
curl -s http://localhost:<容器端口>/health
docker logs <container> --tail 20
docker stats <container> --no-stream
```

### 2. 确认反代转发正常

```bash
# 从外部测试（通过域名）
curl -s -w "HTTP: %{http_code}, Time: %{time_total}s\n" https://<domain>/
# 期望：能拿到响应（哪怕是 401/404），不应该 timeout
```

### 3. 确认客户端能到达

```bash
# 从客户端机器测试
curl -x http://127.0.0.1:<proxy_port> -o NUL -w "Time: %{time_total}s\n" https://<domain>/
# 或在浏览器直接打开 URL，看是否秒返回
```

### 4. 抓实际流量（关键步骤）

如果前 3 步都通但客户端还是报错，**在反代和容器之间插一个 TCP proxy 抓包**：

```python
# /tmp/tcp-proxy.py — 放在 VPS 上运行
import socket, threading, time

def forward(src, dst, label):
    total = 0
    try:
        while True:
            data = src.recv(65536)
            if not data: break
            total += len(data)
            text = data.decode('utf-8', errors='replace')
            print(f'[{time.strftime("%H:%M:%S")}] {label} ({len(data)}B):', flush=True)
            print(text[:2000], flush=True)
            print('---', flush=True)
            dst.sendall(data)
    except Exception as e:
        print(f'[{label}] closed: {e}', flush=True)
    finally:
        try: dst.close()
        except: pass

def handle(client):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect(('127.0.0.1', TARGET_PORT))  # 改成容器端口
    t1 = threading.Thread(target=forward, args=(client, server, 'C>S'), daemon=True)
    t2 = threading.Thread(target=forward, args=(server, client, 'S>C'), daemon=True)
    t1.start(); t2.start(); t1.join()

TARGET_PORT = 8789  # 容器映射端口
LISTEN_PORT = 8790  # proxy 监听端口
listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listener.bind(('0.0.0.0', LISTEN_PORT))
listener.listen(5)
print(f'Proxy :{LISTEN_PORT} -> :{TARGET_PORT}', flush=True)
while True:
    client, addr = listener.accept()
    print(f'\nConn from {addr}', flush=True)
    threading.Thread(target=handle, args=(client,), daemon=True).start()
```

使用方法：
```bash
# 1. 启动 proxy
nohup python3 /tmp/tcp-proxy.py > /tmp/proxy.log 2>&1 &

# 2. 把反代指向 proxy 端口
# Caddy: reverse_proxy localhost:8790
# 重启反代

# 3. 触发客户端操作，查看日志
tail -f /tmp/proxy.log

# 4. 完成后恢复反代端口，杀 proxy
```

## 常见根因速查

### BASE_URL / EXTERNAL_URL 配错

**症状**：服务能连上（WebSocket/登录正常），但某些操作（下载、回调）失败。

**原因**：容器内的 `DB_SYNC_BASE_URL`、`EXTERNAL_URL`、`WEBHOOK_URL` 等配了容器内部地址（如 `http://172.17.0.2:8787` 或 `http://localhost:8787`），server 把这个地址返回给客户端，客户端无法访问。

**诊断**：抓包看 server 返回的 JSON/响应里有没有内部 URL。

**修复**：改成客户端可达的公网地址（如 `https://your-domain.com`）。

**受影响的服务举例**：
- Logseq selfhost: `DB_SYNC_BASE_URL`
- Gitea/Forgejo: `ROOT_URL`
- Minio: `MINIO_SERVER_URL`
- Keycloak: `KC_HOSTNAME`
- n8n: `WEBHOOK_URL`

### 小文件通大文件不通

**可能原因**：
1. 反代 timeout 太短（`proxy_read_timeout`）→ 加超时
2. 反代 body size 限制（`client_max_body_size`）→ 加大限制
3. **不同代码路径**：小文件走路径 A，大文件走路径 B（B 用了错误的 URL）→ 抓包确认

### WebSocket 连上但后续 HTTP 请求失败

**可能原因**：
1. WS 和 HTTP 走不同的端口/路径
2. HTTP 请求的 URL 是 server 动态返回的（可能返回了错误的 URL）
3. Electron `--proxy-server` 只影响 renderer，worker thread 可能不走代理（用 TUN 模式解决）

### Caddy 反代推荐配置（长连接服务）

```caddyfile
your-domain.com {
  request_body {
    max_size 200MB
  }
  reverse_proxy localhost:<port> {
    flush_interval -1
    transport http {
      read_buffer  4MB
      write_buffer 4MB
      dial_timeout 30s
      response_header_timeout 300s
      read_timeout 86400s
      write_timeout 86400s
    }
  }
}
```

### Nginx 反代推荐配置（长连接服务）

```nginx
location / {
    proxy_pass http://localhost:<port>;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_buffering off;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
    client_max_body_size 200M;
}
```

## 排查工具箱

| 工具 | 用途 |
|------|------|
| `docker logs` | 容器内错误 |
| `docker stats --no-stream` | CPU/内存/网络 IO |
| `ss -tn \| grep <port>` | 当前 TCP 连接 |
| `curl -sv` | HTTP 请求详情 |
| `curl -w` | 连接时间分解 |
| TCP proxy（上面的 Python 脚本）| 抓包看实际请求/响应 |
| `journalctl --user -u caddy` | Caddy 错误日志 |

## 时间线法则

如果排查超过 15 分钟还在猜测原因，**立刻插入 TCP proxy 抓包**。大多数问题在看到实际请求/响应后 5 分钟内就能定位。
