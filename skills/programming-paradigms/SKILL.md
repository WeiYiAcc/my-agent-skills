---
name: programming-paradigms
description: "15 大编程范式速查与选型指南。从命令式/声明式基础分类到场景化范式（事件驱动、COP、DSL、并发、数据流、元编程）再到前沿范式（AI原生、云原生）。当需要选择架构模式、评估技术方案、理解某个范式的定位时使用。"
---

# 15 大编程范式：分类、定位与选型

来源：neohope.com 2026-01 整理，本 skill 提炼为 AI 可用的选型参考。

## 一、基础核心范式（所有其他范式的根基）

### 命令式（How — 步骤、状态变更）

| 子范式 | 代表 | 核心 |
|--------|------|------|
| 过程式 | C, BASIC, shell | 顺序步骤 |
| 面向对象 (OOP) | Java, C++, Python | 封装/继承/多态 |
| 面向切面 (AOP) | Spring AOP | 横切关注点（日志/权限/事务） |

### 声明式（What — 描述结果，不管实现）

| 子范式 | 代表 | 核心 |
|--------|------|------|
| 函数式 (FP) | Haskell, Scala, Clojure | 纯函数 + 不可变数据 |
| 逻辑编程 | Prolog, Datalog | 规则推导 |
| 标记式 | HTML, XML, YAML | 结构描述 |

**关键区分**：命令式和声明式不是互斥的 — 一个系统可以命令式编排 + 声明式配置。

## 二、场景化范式（按需求场景选型）

### 约束/契约/规则范式

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 契约式编程 | Eiffel, C# Code Contracts | 前置/后置条件，高可靠系统 |
| 面向约束编程 | CSP 求解器 | 调度、排课、资源分配 |

**在我们的体系中**：ast-grep 规则 = 架构约束编程；workspace.json deps = 依赖契约。

### 事件/策略/插件范式

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 事件驱动 | GUI, Node.js, Pi hooks | 异步响应 |
| 面向策略 | 策略模式, feature flags | 算法热切换 |
| 面向插件 | Pi extensions, OpenCode plugins | 可扩展系统 |

**在我们的体系中**：Pi/OpenCode 的 hook 系统 = 事件驱动 + 插件范式。

### 领域专用 (DSL)

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 外部 DSL | SQL, Makefile, Datalog | 特定领域最优表达 |
| 内部 DSL | bb tasks (Clojure), doit (Python) | 宿主语言内的领域语法 |

**在我们的体系中**：bb.edn tasks = Clojure 内部 DSL；Taskfile.yml = YAML 外部 DSL。

### 面向设计/架构范式

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 面向接口 | Go, Java interface | 模块解耦 |
| 面向组件 (COP) | Spring Bean, **Polylith** | 可复用 brick 组装 |
| 面向服务 (SOP) | 微服务, REST API | 分布式系统 |

**在我们的体系中**：Polylith = COP 的具体实现（lib/ components + bases/ + workspace.json）。

## 三、进阶技术范式

### 并发/异步/分布式

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 多线程 | Java threads, Python threading | CPU 密集 |
| Actor 模型 | Erlang, Akka, Jido (Elixir) | 有状态并发实体 |
| 响应式 | RxJava, Reactor | 数据流 + 背压 |
| CSP | Go goroutine/channel | 通道通信 |

### 数据/状态相关

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 面向数据 | ECS (游戏), Polars | 数据局部性优化 |
| 数据流 | Flink, Spark, doit DAG | 流式/批式计算 |
| 面向状态 | 状态机, Stokowski YAML | 复杂状态转换 |

**在我们的体系中**：doit = 声明式数据流 DAG；Stokowski = 面向状态编程。

### 泛型/元编程

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 泛型 | C++ template, Java/TS generics | 跨类型复用 |
| 元编程 | Clojure macro, Python metaclass | 程序生成程序 |
| 模板 | C++ TMP, Selmer, Jinja2 | 编译期/渲染期代码生成 |

### 开发/测试驱动

| 子范式 | 代表 | 适用 |
|--------|------|------|
| TDD | pytest, jest | 测试先行 |
| 文档驱动 | SKILL.md, AGENTS.md | 文档即规范 |
| 配置驱动 | workspace.json, sops yaml | 配置即代码 |

## 四、前沿新兴范式

### AI 原生开发

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 提示词驱动 (PDD) | Cursor, Copilot, Pi | AI 生成代码 |
| 面向智能体 | Pi subagents, Stokowski | 多 agent 协作 |
| AI 原生语言 | (尚未成熟) | AI-first 语法设计 |

### 云原生/DevOps

| 子范式 | 代表 | 适用 |
|--------|------|------|
| 云原生 | K8s, Docker, Nix | 声明式基础设施 |
| 面向资源 | REST, GraphQL | API 设计 |
| GitOps/DevOps | CI/CD, system-manager | 代码即运维 |

## 五、选型决策树

```
你的问题是什么？
│
├─ "代码怎么组织" → COP (Polylith) + 面向接口
├─ "数据怎么流动" → 数据流 (doit DAG) / 响应式
├─ "状态怎么管理" → 面向状态 (状态机)
├─ "怎么跨平台适配" → 插件范式 + 面向接口
├─ "怎么保证正确性" → 约束/契约 (ast-grep) + TDD
├─ "怎么自动化流程" → 命令式 (shell/Python) + DSL (bb tasks)
├─ "怎么描述配置" → 声明式 (YAML/Nix/workspace.json)
├─ "怎么让 AI 帮忙" → PDD + 面向智能体 + skill 文档驱动
└─ "怎么部署运维" → 云原生 + GitOps
```

## 六、我们的技术栈范式映射

| 工具/系统 | 主范式 | 辅范式 |
|-----------|--------|--------|
| Polylith TS | COP (面向组件) | 约束 (ast-grep) |
| bb.edn tasks | 内部 DSL | 命令式编排 |
| doit (Python) | 数据流 DAG | 声明式 |
| Pi extensions | 事件驱动 + 插件 | 命令式 |
| Stokowski | 面向状态 | 命令式 |
| workspace.json | 声明式配置 | 约束/契约 |
| Nix/home-manager | 声明式 + 函数式 | 云原生 |
| SKILL.md | 文档驱动 | PDD |
| ariadne-fact | 逻辑编程 (Datalog) | 面向数据 |
