---
name: jet-data-format
description: "jet (edn/json/yaml 互转) + sops 加密 + universal config schema。当需要在 edn/json/yaml 之间转换数据、操作 sops 加密的配置文件、或编写跨格式通用配置时使用。"
---

# jet-data-format — 跨格式数据转换与加密配置

## 何时触发

- edn / json / yaml 之间互转
- 操作 sops 加密的 yaml/json 配置
- 新建或修改遵循 universal config schema 的配置文件
- review 配置时需要切换视图格式
- chezmoi secrets 管理

---

## jet 基础

已安装：`jet v0.7.27`（babashka 生态，Clojure 数据处理）

### 格式转换

```bash
# edn → json
cat file.edn | jet -i edn -o json

# json → yaml
cat file.json | jet -i json -o yaml

# yaml → edn
cat file.yaml | jet -i yaml -o edn

# json → edn (pretty)
cat file.json | jet -i json -o edn
```

### 数据变换（thread-last）

```bash
# 取某个 key
echo '{:a 1 :b 2}' | jet -t ':a'

# 取嵌套 key
echo '{:linear {:api_key "x"}}' | jet -t ':linear :api_key'

# select-keys
echo '{:a 1 :b 2 :c 3}' | jet -t '(select-keys [:a :b])'

# 过滤 vector
echo '[{:name "a" :v 1} {:name "b" :v 2}]' | jet -t '(filter (fn [x] (> (:v x) 1)))'
```

### 常用 flags

| flag | 作用 |
|---|---|
| `-i edn/json/yaml` | 输入格式（默认 edn） |
| `-o edn/json/yaml` | 输出格式（默认 edn） |
| `-t` | thread-last 表达式 |
| `-T` | thread-first 表达式 |
| `-f` | 自定义 Clojure 函数 |
| `-k` | keywordize JSON/YAML keys |
| `--no-pretty` | 紧凑输出 |
| `-c` | collect 多个值为 vector |

---

## Universal Config Schema

所有配置文件（secrets、env、service config）遵循同一个 schema，确保 edn/json/yaml 三格式无损互转。

### 规则

1. **顶层是 map**（不是 array/vector）
2. **key 只用 string**（不用 keyword/symbol，确保 json 兼容）
3. **value 只有两种类型**：string 或嵌套 map
4. **没有 array/list/vector**（array 不能作为 JSON object key，转换有歧义）
5. **嵌套最多 2 层**（group → key → value）
6. **key 命名**：SCREAMING_SNAKE_CASE（环境变量风格）或 kebab-case（服务名）
7. **group 命名**：小写 snake_case（分类语义，如 `linear`、`ai_memory`）

### 示例（三种视图等价）

**YAML（存储格式，sops 友好）：**
```yaml
linear:
  LINEAR_API_KEY: "lin_api_xxx"
search:
  JINA_API_KEY: "jina_xxx"
ai_memory:
  AI_MEMORY_AUTH_TOKEN: "2e6af_xxx"
  AI_MEMORY_SERVER_URL: "https://ai-memory.wyrunning.dpdns.org"
ariadne_fact:
  ARIADNE_API_KEY: "xxx"
  ARIADNE_FACT_URL: "http://104.168.22.124:7735"
```

**JSON（等价）：**
```json
{
  "linear": {
    "LINEAR_API_KEY": "lin_api_xxx"
  },
  "search": {
    "JINA_API_KEY": "jina_xxx"
  },
  "ai_memory": {
    "AI_MEMORY_AUTH_TOKEN": "2e6af_xxx",
    "AI_MEMORY_SERVER_URL": "https://ai-memory.wyrunning.dpdns.org"
  }
}
```

**EDN（等价）：**
```clojure
{"linear" {"LINEAR_API_KEY" "lin_api_xxx"}
 "search" {"JINA_API_KEY" "jina_xxx"}
 "ai_memory" {"AI_MEMORY_AUTH_TOKEN" "2e6af_xxx"
              "AI_MEMORY_SERVER_URL" "https://ai-memory.wyrunning.dpdns.org"}}
```

### 验证互转无损

```bash
# yaml → json → edn → yaml 循环验证
cat secrets.yaml | sops decrypt /dev/stdin 2>/dev/null | \
  jet -i yaml -o json | jet -i json -o edn | jet -i edn -o yaml
```

---

## sops + YAML 操作

### 查看（解密 → 转格式）

```bash
# 看 yaml 明文
sops decrypt secrets.yaml

# 看 edn 视图
sops decrypt secrets.yaml | jet -i yaml -o edn

# 看 json 视图
sops decrypt secrets.yaml | jet -i yaml -o json

# 查单个分组
sops decrypt secrets.yaml | jet -i yaml -t '(get "ai_memory")' -o edn
```

### 编辑

```bash
# 交互式编辑（解密 → $EDITOR → 重加密，只改动的字段 IV 变化）
sops secrets.yaml

# 单字段修改（最小 diff）
sops set secrets.yaml '["group"]["KEY_NAME"]' '"new_value"'

# 删除字段
sops unset secrets.yaml '["group"]["KEY_NAME"]'
```

### 新建 sops 文件

```bash
# 先写明文 yaml，再加密
cat > secrets.yaml << 'EOF'
group_name:
  KEY_NAME: "value"
EOF
sops encrypt --in-place secrets.yaml
```

### diff 特性

- `sops set/unset` 只改变目标字段的密文 + mac + lastmodified（2-3 行噪音）
- `sops edit`（交互式）同理，只有编辑过的字段密文变化
- AI diff 能看到：key 名增删、分组结构变化
- AI diff 看不到：value 内容（加密了，这是预期行为）

---

## chezmoi 集成

### 文件布局

```
~/.local/share/chezmoi/
  .sops.yaml                          # sops 规则
  dot_pi/agent/secrets.yaml           # 所有 secret（sops 加密）
  dot_pi/agent/mcp.json.tmpl          # 引用 secrets
  dot_config/secrets/api-keys.env.tmpl  # 引用 secrets 渲染 env
```

### template 中引用

```gotemplate
{{- $secrets := output "sops" "decrypt" (joinPath .chezmoi.sourceDir "dot_pi/agent/secrets.yaml") | fromYaml -}}

# 取嵌套 key
{{ (index $secrets "ai_memory").AI_MEMORY_AUTH_TOKEN }}

# 取顶层 group 下的 key
{{ (index $secrets "linear").LINEAR_API_KEY }}
```

### .sops.yaml

```yaml
creation_rules:
  - path_regex: .*secrets\.yaml$
    age: <recipient>
```

---

## 与 Nix 配置的关系

此 schema 的嵌套 map（string → string | map）结构等价于 Nix 的 attrset：

```nix
# Nix 等价
{
  linear = {
    LINEAR_API_KEY = "...";
  };
  ai_memory = {
    AI_MEMORY_AUTH_TOKEN = "...";
  };
}
```

未来如果需要从 secrets.yaml 生成 Nix 配置片段：

```bash
sops decrypt secrets.yaml | jet -i yaml -o json | nix eval --json --file -
# 或用 yq/jq 做简单变换
```

---

## 注意事项

- **禁止在 secrets.yaml 中使用 array**：会破坏三格式互转的等价性
- **非 secret 值**：key 名加 `_unencrypted` 后缀，sops 不加密该字段
- **sops decrypt 输出到管道是安全的**：不落盘，不入 shell history
- **jet 的 keyword**：`-k` flag 会把 string key 转为 keyword（`:linear`），仅用于 edn 阅读视图，不要写回 yaml/json
