---
name: polylith-clj
description: "所有 Clojure 项目默认使用 Polylith 架构。核心规则：base 只能是入口胶水（只调用 component），业务逻辑必须写在 components/ 里，新功能 = 新 component。工具链：poly CLI + bb.edn 作为任务编排入口（对应 Python 的 Taskfile）。"
---

# Polylith Clojure

## 核心规则

- **base = 入口胶水**：`bases/` 下只放入口逻辑（main、CLI 解析、路由），只调用 component，不含业务逻辑
- **component = 业务逻辑**：所有业务逻辑写在 `components/` 里，可复用，可独立测试
- **新功能 = 新 component**：需要新功能时，先建 component，再在 base 里加一行调用
- **bb.edn = 任务编排入口**：对应 Python Polylith 的 Taskfile，DAG 依赖、并行执行都在这里定义

## 目录结构

```
<workspace>/
├── bases/
│   └── <namespace>/
│       └── <base-name>/
│           └── core.clj      ← 只有入口，调用 component
├── components/
│   └── <namespace>/
│       └── <component-name>/
│           ├── core.clj      ← 业务逻辑
│           └── interface.clj ← 对外接口（Polylith 约定）
├── projects/
│   └── <project>/
│       └── deps.edn          ← 声明依赖的 bricks
├── development/
│   └── deps.edn
├── deps.edn                  ← workspace 根级依赖
├── workspace.edn             ← Polylith 配置
└── bb.edn                    ← Babashka 任务编排（DAG 入口）
```

## poly CLI 命令

```bash
poly info          # workspace 概览，显示所有 brick 和 project
poly check         # 校验依赖图（无输出 = 通过）
poly deps          # 可视化 brick 间依赖
poly libs          # 第三方库使用情况
poly diff          # 对比最新 git tag 变更的 brick
poly test          # 按 diff 范围运行受影响测试
poly create component --name <name>   # 新建 component
poly create base --name <name>        # 新建 base
poly create project --name <name>     # 新建 project
```

## bb.edn 任务编排

bb.edn 是 Clojure Polylith 的任务编排入口，对应 Python 的 Taskfile：

```clojure
{:tasks
 {:requires ([babashka.fs :as fs])

  ;; DAG 依赖
  build    {:depends [test]
            :task (shell "clojure -T:build uber")}

  test     {:task (shell "poly test")}

  ;; 并行执行
  check    {:task (run 'poly-check)}
  poly-check {:task (shell "poly check")}}}
```

常用命令：
```bash
bb tasks          # 列出所有任务
bb build          # 构建
bb test           # 测试
bb check          # poly check
```

## 已知 Workspace

| workspace | 路径 | namespace | 用途 |
|---|---|---|---|
| ariadne-fact | `~/ghq/github.com/WeiYiAcc/ariadne-fact/` | - | facts DataScript server + pi 扩展 |
| my-toolbox/my-clj | `~/ghq/github.com/WeiYiAcc/ariadne-fact/my-toolbox/my-clj/` | - | Ariadne 工具链（logseq-db 等） |

## 与 Python Polylith 的对应关系

| Python | Clojure | 说明 |
|---|---|---|
| `uv run poly` | `poly` | Polylith CLI |
| `Taskfile.yml` | `bb.edn` | 任务编排入口 |
| `components/ns/brick/core.py` | `components/ns/brick/core.clj` | 业务逻辑 |
| `bases/ns/brick/core.py` | `bases/ns/brick/core.clj` | 入口胶水 |
| `uv run poly sync` | `poly check` + 手动更新 deps.edn | 同步依赖 |
| `PYTHONPATH=components:bases` | deps.edn `:local/root` 路径 | 运行时路径 |

## 违规示例（不要这样做）

```clojure
;; ❌ 错误：在 base 里写业务逻辑
(ns myapp.cli.core)
(defn process-data [data]
  ;; 100 行业务逻辑...
  )
(defn -main [& args]
  (process-data (read-input args)))

;; ✅ 正确：base 只调用 component
(ns myapp.cli.core
  (:require [myapp.processor.core :as processor]))
(defn -main [& args]
  (processor/process (read-input args)))
```
