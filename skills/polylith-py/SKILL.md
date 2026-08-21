---
name: polylith-py
description: "所有 Python 项目默认使用 Polylith 架构。核心规则：base 只能是 CLI 胶水（每个命令 ≤10 行，只调用 component），业务逻辑必须写在 components/ 里，新功能 = 新 component。新代码用 pydantic frozen model + 纯函数。dodo.py(doit) 声明式编排任务 DAG。Use `uv run poly` for brick management, `uv add` for deps."
---

## Quick Reference

两个 workspace 行为一致，`poly` 命令都不需要 PYTHONPATH：

```bash
uv run poly info     # Workspace 概览
uv run poly check    # 校验依赖图（无输出=通过）
uv run poly deps     # 可视化 brick 间依赖
uv run poly libs     # 第三方库使用 + project 版本声明
uv run poly diff     # 对比最新 git tag 变更的 brick（需先打 tag）
uv run poly sync     # 自动补全 pyproject.toml 缺失的 brick 引用
uv run poly test     # 按 diff 范围运行受影响测试
```

运行业务代码时两个 workspace 都需要 PYTHONPATH：

```bash
PYTHONPATH=components:bases uv run python -m <namespace>.<brick>
```

## Workspaces

| workspace | 路径 | namespace | 用途 |
|---|---|---|---|
| my-tools/my-py | `~/ghq/github.com/WeiYiAcc/my-tools/my-py/` | `toolbox` | 通用工具库（无数据） |
| subsidy-2026 | `~/ghq/github.com/WeiYiAcc/subsidy-2026/` | `subsidy` | 产业奖补 ETL + CCDS 数据目录 |

### my-tools/my-py

| 配置 | 值 |
|------|-----|
| namespace | `toolbox` |
| theme | `loose` |
| 包管理 | uv（`uv.lock`） |
| Python | ≥ 3.13 |
| PYTHONPATH | `poly` 命令不需要，运行代码需要 `PYTHONPATH=components:bases` |

### subsidy-2026

| 配置 | 值 |
|------|-----|
| namespace | `subsidy` |
| theme | `loose` |
| 包管理 | uv（`uv.lock`） |
| Python | ≥ 3.13 |
| 运行方式 | `PYTHONPATH=components:bases uv run python -m subsidy.etl` |
| task runner | `task`（Taskfile.yml，替代 Makefile） |

## Polylith Structure

```
<workspace>/
├── components/          # 可复用功能砖
│   └── <namespace>/
│       └── <brick_name>/
│           ├── __init__.py
│           └── core.py
├── bases/               # 应用入口砖（CLI 等）
│   └── <namespace>/
│       └── <brick_name>/
├── projects/            # 部署单元（不含业务代码）
│   └── <project>/
│       └── pyproject.toml   # 声明依赖的 bricks
├── development/         # 开发实验区
├── tests/               # loose theme: test 在根级
├── pyproject.toml       # 根级依赖
├── workspace.toml       # Polylith 配置（namespace 在这里）
└── uv.lock
```

### subsidy-2026 额外目录（CCDS）

```
subsidy-2026/
├── data/                # CCDS 数据目录（不属于 Polylith）
│   ├── raw/             # 手录表、各户原始申报表、归档
│   ├── interim/         # DONE/TODO/DOING 户文件夹
│   ├── processed/       # master.csv、汇总表
│   └── external/        # 政策文件、模板
└── Taskfile.yml         # go-task DAG（替代 Makefile）
```

## Create Bricks

```bash
uv run poly create component --name excel_parser
uv run poly create base --name data_cli
uv run poly create project --name my_service
```

创建后运行 `PYTHONPATH=components:bases uv run poly sync` 同步 pyproject.toml。

## Dependencies

```bash
uv add requests                        # 添加根级依赖
uv add --dev pytest                    # 添加开发依赖
uv run poly sync                       # 同步 brick 到 pyproject.toml
uv lock                                # 更新 lockfile
```

## Run & Test

```bash
# my-tools/my-py
uv run python -m toolbox.st_ink_cli.core    # 运行 base
uv run pytest                               # 运行所有测试
uv run poly test                            # 按 diff 运行受影响测试

# subsidy-2026
task all                                    # 完整 DAG
task build-master                           # 手录表 → master.csv
task gen-md                                 # 生成 materials.md
task gen-summary                            # 生成汇总表
task status                                 # 查看户数和 master.csv 状态
PYTHONPATH=components:bases uv run pytest   # 运行测试
```

## Standalone Scripts

不在 polylith 结构内的独立脚本用 inline metadata：

```python
# /// script
# requires-python = ">=3.13"
# dependencies = ["requests"]
# ///
```

运行：`uv run script.py`

## Key Rules

- **base = CLI 胶水**：`bases/` 下的 `core.py` 只允许写 `@app.command` 定义，每个命令 ≤10 行，只调用 component。**业务逻辑一律写在 `components/` 里**。
- **新功能 = 新 component**：需要新功能时，先用 `uv run poly create component --name <name>` 建 brick，再在 base 里加一行调用。
- **不用 pip/poetry/pdm** — 一律 `uv`
- **代码只写在 bricks 里**（components/ 或 bases/），projects/ 只放配置
- **brick 内引用**：`from <namespace>.<brick_name>.core import ...`
- **新 brick 后**必须 `PYTHONPATH=components:bases uv run poly sync` 刷新 pyproject.toml
- **loose theme**：test 目录在仓库根级，不在 brick 内
- **`poly` 命令不需要 PYTHONPATH**——poly 做静态分析，直接读文件系统不 import 模块
- **运行业务代码时两个 workspace 都需要 `PYTHONPATH=components:bases`**
- **`poly check` 无输出 = 通过**，有输出 = 有错误
- **`poly deps`** 可快速发现未被任何 brick 使用的孤立 component

## Component 编写规范（新代码）

新 component 采用函数式风格 + pydantic frozen model：

```python
# components/subsidy/manifest/core.py
from pydantic import BaseModel
from pathlib import Path


# ── 不可变数据模型 ────────────────────────────────
class ImageEntry(BaseModel, frozen=True):
    hash: str
    index: int


class ManifestEntry(BaseModel, frozen=True):
    hash: str
    filename: str
    path: str = ""
    images: list[ImageEntry] = []
    ts: str = ""
    note: str = ""


# ── 纯函数（无副作用，输入→输出）────────────────
def scan_docx(path: Path) -> ManifestEntry:
    """input: docx path → output: manifest entry with image hashes"""
    ...


def verify(a_entries: list[ManifestEntry], b_entries: list[dict]) -> list[dict]:
    """input: 两份 manifest → output: 校验结果"""
    ...
```

### 规则：

- **新 component 用 pydantic `frozen=True` model**，旧代码暂不改
- **函数签名显式声明输入输出类型**，不用裸 dict
- **副作用（文件写入、API 调用）推到 base 层或通过参数注入**
- IO 边界多、外部数据脏 → pydantic（运行时验证）
- 纯计算、内部逻辑 → `dataclasses(frozen=True)` 也可

## doit 任务编排（dodo.py）

`dodo.py` 是声明式的任务 DAG，不包含业务逻辑：

```python
# dodo.py
def task_extract_验收图():
    """声明式：输入、输出、action"""
    return {
        "file_dep": ["data/interim/验收图片/三合村/*.docx"],  # 输入变了才重跑
        "targets": ["data/interim/验收图片/三合村/extracted/manifest.jsonl"],
        "actions": [f"{POLY} -m subsidy.photos extract"],  # 调用 base CLI
        "verbosity": 2,
    }

def task_scan_验收图():
    return {
        "file_dep": [所有户级验收图_docx],
        "targets": [所有户级_manifest_jsonl],
        "actions": [f"{POLY} -m subsidy.photos scan"],
        "task_dep": ["extract_验收图"],  # 依赖
    }

def task_verify_验收图():
    return {
        "file_dep": ["extracted/manifest.jsonl", 户级_manifests],
        "targets": ["verify_report.jsonl"],
        "actions": [f"{POLY} -m subsidy.photos verify"],
        "task_dep": ["scan_验收图"],
    }
```

### 规则：

- **dodo.py 只做编排**，不 import component，不包含业务逻辑
- **声明 `file_dep` + `targets`** → doit 自动增量构建
- **`actions` 只调用 base CLI**（`python -m subsidy.xxx`）
- **`task_dep`** 声明任务间依赖顺序
- doit 不侵入 poly 架构，只是 dodo.py 一个文件

## 架构分层总览

```
dodo.py              ← 声明式：目标 + 依赖（what）
  ↓ shell 调用
bases/typer CLI       ← 命令式：执行步骤（how，≤10行）
  ↓ import
components/           ← 函数式：纯函数 + pydantic frozen model（可复用逻辑，无副作用）
```

- doit “做什么”，base “怎么做”，component “具体算法”
- manifest/state/data jsonl 是层间通信的媒介（不是函数调用）

### typer 在 base 层的定位

typer CLI 是 doit 和 component 之间的**架构边界**，不是可有可无的薄壳：

```
dodo.py → shell: "python -m subsidy.photos scan" → typer CLI → import component
```

为什么 doit 必须通过 typer CLI 调用，而不是直接 import component：

1. **进程隔离** — 每个 task 是独立进程，崩了不影响 doit 本身
2. **参数显式** — `python -m subsidy.photos scan --limit 5`，可复制到终端复现
3. **日志分离** — stdout/stderr 自然隔离，doit 可捕获
4. **poly check 追踪** — base → component 的 import 链清晰，dodo.py 不侵入依赖图
5. **一致性** — 人手动跑和 doit 跑是同一条路径

如果 dodo.py 直接 import component，dodo.py 就变成了另一个 base，poly 依赖图乱了。
