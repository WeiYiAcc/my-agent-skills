---
name: yaml
description: >
  YAML 作为配置和数据存储格式的写法规范。涵盖安全写法规则（frontmatter、引号、特殊字符）、
  注释约定、YAML 作为带注释 JSON/EDN 替代品的定位、与 sops 加密配合、kcl/cue 校验集成。
  当写 YAML 文件、写 SKILL.md frontmatter、讨论配置格式选型、需要 kcl/cue 校验 YAML 时触发。
  格式互转操作（edn/json/yaml）见 skill:jet-data-format。sops 加密操作见 skill:encryption。
---

# YAML — 存储格式规范与安全写法

## 定位

YAML 在本环境中的角色：

| 用途 | 为什么用 YAML |
|------|-------------|
| 配置文件 | 带注释的 JSON 替代品，人可读 |
| AI 可读的结构化数据 | 比 JSON 支持注释，比 TOML 支持深嵌套 |
| edn/Clojure 数据的中间格式 | edn 无注释，YAML 可以加注释后通过 jet 转回 edn |
| sops 加密载体 | sops 原生支持 YAML 的字段级加密 |

**不适合 YAML 的场景：**
- 需要精确 schema 强制执行 → 用 kcl/cue 校验 YAML（而非换格式）
- 纯机器交换 → 用 JSON
- Clojure 代码内 → 用 edn

---

## 安全写法规则

### 字符串值（最常出错的地方）

```yaml
# ✅ 推荐：> 折叠块（长文本、含特殊字符）
description: >
  当用户说「记住这个」时触发。支持 PDF、DOCX: 全格式。
  冒号、引号、#号都不需要转义。

# ✅ 安全：无特殊字符的短值不加引号
name: my-skill
version: 1.0.0

# ✅ 安全：需要保留换行用 |
body: |
  第一行
  第二行

# ⚠️ 谨慎：双引号包裹（纯英文 + \" 转义内嵌引号时可用）
desc: "Use when user says \"hello\""

# ❌ 危险：双引号内含中文引号
desc: "当用户说"记住"时"  # 解析失败！

# ❌ 危险：值以特殊字符开头但没加引号
value: {not_a_map}   # 被解析为 map
value: [not_a_list]  # 被解析为 list
value: *anchor       # 被解析为 alias
value: #comment      # 被解析为空+注释
```

### YAML 特殊字符速查

以下字符出现在**值的开头**时必须加引号或用块标量：

| 字符 | 含义 | 解法 |
|------|------|------|
| `:` + 空格 | mapping | 用引号或 `>` |
| `#` | 注释 | 用引号或 `>` |
| `{` `}` | flow mapping | 用引号 |
| `[` `]` | flow sequence | 用引号 |
| `*` `&` | anchor/alias | 用引号 |
| `!` | tag | 用引号 |
| `\|` `>` | 块标量指示符 | 用引号（罕见） |
| `"` `'` | 引号本身 | 用另一种引号或 `>` |

### Frontmatter 专项规则

SKILL.md、markdown 博文等文件的 YAML frontmatter：

```yaml
---
name: my-skill
# description 统一用 > 折叠块，永远安全
description: >
  长描述，随便写什么字符。中文引号「」、冒号、#号全部安全。
  多行会被折叠为一行。
---
```

为什么不用双引号：中文全角引号 `""` 在某些 YAML 解析器中被 Unicode 折叠为 ASCII `""`，导致字符串提前终止。

---

## 注释约定

YAML 注释是它相比 JSON 的核心优势。约定：

```yaml
# === 分组标题（用 === 分隔大块） ===

# 行上注释：解释为什么
api_key: "xxx"  # 行尾注释：解释是什么

# 多行注释（没有 /* */ 语法，每行加 #）
# 这个配置用于 ai-memory 远程服务器连接。
# 当服务部署在 homelab 时需要 bearer token 认证。
ai_memory:
  server_url: "https://ai-memory.wyrunning.dpdns.org"
  auth_token: "ENC[AES256_GCM,...]"  # sops 加密
```

**注释不参与数据转换**：`jet -i yaml -o json` 会丢失注释。如果注释很重要，保留 YAML 作为 source of truth，其他格式只作为视图。

---

## 与其他 skill 的关系

| 需求 | 用哪个 skill |
|------|-------------|
| edn/json/yaml 互转 | skill:jet-data-format |
| sops 加密/解密 YAML | skill:encryption + skill:jet-data-format |
| 写 SKILL.md frontmatter | 本 skill（安全写法规则） |
| 校验 YAML schema | 本 skill（kcl/cue 章节，待补充） |
| 配置文件的 schema 设计 | skill:jet-data-format（universal config schema） |

---

## kcl / cue 校验（预留）

未来补充。两者都用于校验 YAML 数据结构是否符合预期 schema。

### kcl（蚂蚁开源）
- 强类型，Python 风格语法
- `kcl vet schema.k data.yaml`

### cue（Go 生态）
- 基于值格的类型系统
- `cue vet schema.cue data.yaml`

具体工作流待实际使用场景积累后补充。

---

## 常见陷阱

1. **布尔值陷阱**：`yes`/`no`/`on`/`off`/`true`/`false` 在 YAML 1.1 中自动转为布尔。要保留字符串需加引号：`"yes"`
2. **数字开头的字符串**：`007` 被解析为整数 7。要保留前导零需加引号
3. **空值**：`key:` 后面什么都不写 = null，不是空字符串。空字符串要写 `key: ""`
4. **缩进必须用空格**：Tab 在 YAML 中是非法字符
5. **多文档**：`---` 分隔多个文档，不要和 frontmatter 的 `---` 混淆
