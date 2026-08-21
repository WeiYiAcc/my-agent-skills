# YAML Frontmatter 安全写法

完整规范见 **skill:yaml**（安全写法规则 → Frontmatter 专项规则）。

核心规则：中文 description 统一用 `>` 折叠块，不用双引号包裹。

```yaml
---
name: my-skill
description: >
  内容随便写，不需要转义任何字符。
---
```
