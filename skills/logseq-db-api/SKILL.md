---
name: logseq-db-api
description: 通过 HTTP API（端口 12315）操作 Logseq DB 版图谱。涵盖 block 增删改、property 设置、class tag 操作、批量写入。前提：WSL socat 转发 12315、Logseq HTTP API server 已开启。Schema 信息见关联 skill logseq-db-schema。
---

# Logseq DB 版 HTTP API 操作

关联：property ident 和 class 定义见 `logseq-db-schema` skill。

## 前提条件

1. Logseq 设置 → Features → Enable HTTP APIs server → 已开启
2. WSL `wsl-port-forward.service` active（socat 转发 12315）
3. API：`http://127.0.0.1:12315/api`
4. Token：空 Bearer

## 调用格式

```bash
curl -s -m 10 "http://127.0.0.1:12315/api" \
  -H "Authorization: Bearer " \
  -H "Content-Type: application/json" \
  -d '{"method": "METHOD", "args": [...]}'
```

## 数据录入（两种方案）

### 方案1：Journal Block（推荐）

和手动在 journal 录入一致，class 表格视图正常显示。

```python
# 1. 在 journal 下创建 block（纯名字，不加 #tag）
result = api_call("logseq.editor.insertBlock",
    ["jun 11th, 2026", "韦建贞", {"isPageBlock": True}])
uuid = json.loads(result)["uuid"]

# 2. 设置 class tag（通过 :block/tags，不是在 title 里加文本）
api_call("logseq.editor.upsertBlockProperty",
    [uuid, ":block/tags", "跨省交通补"])

# 3. 设置 property（必须用 ident，见 logseq-db-schema skill）
api_call("logseq.editor.upsertBlockProperty",
    [uuid, ":user.property/shenqingbiao", True])
```

### 方案2：独立 Page

适合需要子内容的实体。

```python
result = api_call("logseq.editor.createPage",
    ["廖佳玉", None, {"createFirstBlock": False}])
uuid = json.loads(result)["uuid"]

api_call("logseq.editor.upsertBlockProperty",
    [uuid, ":block/tags", "跨省交通补"])
api_call("logseq.editor.upsertBlockProperty",
    [uuid, ":user.property/shenqingbiao", True])
```

## 查询

```bash
# 当前图谱
{"method": "logseq.app.getCurrentGraph", "args": []}

# 所有页面
{"method": "logseq.editor.getAllPages", "args": []}

# 页面 block 树
{"method": "logseq.editor.getPageBlocksTree", "args": ["页面名"]}

# 单个 block（含 DB properties）
{"method": "logseq.editor.getBlock", "args": ["UUID"]}

# Datalog
{"method": "logseq.db.q", "args": ["[:find ?title :where [?e :block/title ?title]]"]}
```

## 写入/修改

```bash
# 插入 block
{"method": "logseq.editor.insertBlock", "args": ["页面名", "内容", {"isPageBlock": true}]}

# 修改内容
{"method": "logseq.editor.updateBlock", "args": ["UUID", "新内容"]}

# 删除 block
{"method": "logseq.editor.removeBlock", "args": ["UUID"]}

# 创建页面
{"method": "logseq.editor.createPage", "args": ["名称", null, {"createFirstBlock": false}]}

# 删除页面
{"method": "logseq.editor.deletePage", "args": ["页面名"]}
```

## Property 设置规则

```bash
# ✅ 用 ident（立即返回 null）
{"method": "logseq.editor.upsertBlockProperty", "args": ["UUID", ":user.property/wugongzhengming", true]}

# ✅ 设置 class tag
{"method": "logseq.editor.upsertBlockProperty", "args": ["UUID", ":block/tags", "跨省交通补"]}

# ❌ 用中文名（永久 hang，不返回）
{"method": "logseq.editor.upsertBlockProperty", "args": ["UUID", "务工证明", true]}
```

## 查找新 Property 的 Ident

```bash
# 1. getAllPages → 筛选 uuid 以 00000002- 开头的
# 2. getBlock(uuid) → 读 "ident" 字段
```

## 批量写入模板

```python
import openpyxl, json, subprocess

API = "http://127.0.0.1:12315/api"

def api_call(method, args):
    data = json.dumps({"method": method, "args": args})
    result = subprocess.run(
        ["curl", "-s", "-m", "10", API,
         "-H", "Authorization: Bearer ",
         "-H", "Content-Type: application/json",
         "-d", data],
        capture_output=True, text=True)
    return result.stdout

# 每条记录：insert → tag → properties
result = api_call("logseq.editor.insertBlock",
    [JOURNAL_PAGE, name, {"isPageBlock": True}])
uuid = json.loads(result)["uuid"]
api_call("logseq.editor.upsertBlockProperty", [uuid, ":block/tags", CLASS_NAME])
api_call("logseq.editor.upsertBlockProperty", [uuid, PROP_IDENT, value])
```

## 注意事项

1. **title 只放人类可读内容** — 不混入 #tag 或 property 文本
2. **Class tag 用 `:block/tags` 设置** — 不在 title 里写 `#className`
3. **Property 必须用 ident** — 中文名导致永久 hang
4. **insertBlock parent 用页面名** — 用 UUID 会产生 `#[[uuid]]` 错误引用
5. **createPage 参数**：`[name, null, {"createFirstBlock": false}]` — 否则超时
6. **Journal 页面名格式**：`jun 11th, 2026`（小写英文月份 + 序数词）
7. **graphthulhu-logseq MCP 不支持 DB 版 property** — 只能走 HTTP API
