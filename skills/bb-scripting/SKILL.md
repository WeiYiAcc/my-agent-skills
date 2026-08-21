---
name: bb-scripting
description: Babashka (bb) 脚本开发速查。内置库清单、bb.edn 模式、tasks 透传模式、常见坑。用于 AI 写 bb 脚本时避免 deps 错误和反模式。
---

# bb-scripting — Babashka 脚本开发速查

## 何时触发

- 要写 `bb.edn` tasks 或 bb 脚本
- 需要查 bb 内置了哪些库（避免加不必要的 `:deps`）
- polylith 风格的 bb 项目结构设计
- `~/bb.edn` 全局透传入口编写

---

## bb 版本

当前安装：**bb 1.12.217**（GraalVM native-image，无需 JVM）

---

## 内置库（不需要 :deps）

**关键规则**：下列库全部内置，bb.edn 里 **不要** 写进 `:deps`，否则会触发 Maven 下载（需要 Java 且很慢）。

### babashka 自带 ns

| namespace | 用途 |
|---|---|
| `babashka.process` | 执行外部命令（`shell`, `process`）|
| `babashka.fs` | 文件系统操作（比 java.io.File 好用）|
| `babashka.http-client` | HTTP 客户端 |
| `babashka.http-client.websocket` | WebSocket |
| `babashka.curl` | curl 封装（简单场景） |
| `babashka.cli` | CLI 参数解析 |
| `babashka.deps` | 运行时加载依赖 |
| `babashka.pods` | Pod 协议（进程外扩展） |
| `babashka.signal` | Unix 信号处理 |
| `babashka.tasks` | task runner 内部 API |
| `babashka.terminal` | 终端能力检测 |
| `babashka.wait` | 等待端口/条件 |
| `babashka.nrepl.server` | 内置 nREPL |

### 第三方库（已内置）

| namespace | 库 | 用途 |
|---|---|---|
| `cheshire.core` | cheshire | **JSON 解析/生成** |
| `clj-yaml.core` | clj-yaml | YAML 解析 |
| `clojure.data.csv` | data.csv | CSV 读写 |
| `clojure.data.xml` | data.xml | XML 解析 |
| `cognitect.transit` | transit | Transit 格式 |
| `clojure.tools.cli` | tools.cli | CLI 参数解析 |
| `clojure.tools.logging` | tools.logging | 日志 |
| `taoensso.timbre` | timbre | 高级日志 |
| `edamame.core` | edamame | Clojure 代码解析 |
| `rewrite-clj.*` | rewrite-clj | Clojure 代码重写 |
| `selmer.*` | selmer | 模板引擎 |
| `hiccup.core` / `hiccup2.core` | hiccup | HTML 生成 |
| `org.httpkit.client` | http-kit | 异步 HTTP |
| `org.httpkit.server` | http-kit | HTTP 服务器 |
| `nextjournal.markdown` | markdown | Markdown 解析 |
| `flatland.ordered.map` | ordered | 有序 map |
| `clojure.core.async` | core.async | CSP 并发 |
| `clojure.core.match` | core.match | 模式匹配 |
| `clojure.test.check` | test.check | 生成式测试 |

### Clojure 标准库（已内置）

`clojure.string` `clojure.set` `clojure.walk` `clojure.zip` `clojure.edn` `clojure.pprint` `clojure.data` `clojure.java.io` `clojure.java.shell` `clojure.math` `clojure.test` `clojure.repl` `clojure.stacktrace` `clojure.data.priority-map` `clojure.core.rrb-vector`

### Java 类（可直接用）

`java.time.*`（Instant, ZonedDateTime, LocalDate, DateTimeFormatter 等）、`java.io.File`、`java.nio.file.Path`、`java.nio.file.Files`、`java.net.URI`、`java.net.URL`、`java.util.Base64`、`java.util.regex.Pattern`、`javax.net.ssl.SSLContext`

---

## bb.edn 核心模式

### 基本结构

```clojure
{:paths ["src" "components/foo/src"]  ;; classpath
 ;; :deps {}  ← 尽量不用！大多数场景内置库够了
 :tasks
 {:requires ([my.ns :as x])  ;; 全局 require，所有 task 共享

  task-name {:doc  "说明"
             :task (x/do-something *command-line-args*)}

  with-deps {:doc    "有依赖的 task"
             :depends [task-name]
             :task   (println "after task-name")}}}
```

### tasks 特殊绑定

| 绑定 | 类型 | 说明 |
|---|---|---|
| `*command-line-args*` | seq of string | 当前 task 的命令行参数 |
| `*input*` | string | 前一个 task 的输出（管道模式） |

### 透传模式（关键模式）

场景：`~/bb.edn` 作为全局入口，转发到各子项目。

```clojure
;; ~/bb.edn — 全局入口
{:tasks
 {repo
  {:doc  "转发到 my-repo-sync"
   :task (let [home (System/getenv "HOME")]
           (apply shell {:dir (str home "/my-repo-sync")}
                  "bb" *command-line-args*))}}}
```

用法：`cd ~ && bb repo status infra`
等价：`cd ~/my-repo-sync && bb status infra`

**坑**：如果在子项目目录内跑 `bb repo ...`，bb 读的是子项目的 bb.edn 而非 `~/bb.edn`。
**解法**：子项目 bb.edn 里也加一个同名 task 透传自己：

```clojure
;; ~/my-repo-sync/bb.edn
{:tasks
 {:requires ([my.cli :as cli])

  status {:task (cli/status *command-line-args*)}

  ;; 兼容 bb repo status 写法
  repo {:doc "透传自己"
        :task (apply cli/-main *command-line-args*)}}}
```

### Polylith 风格 :paths

```clojure
{:paths ["components/repo-registry/src"   ;; component
         "components/git-ops/src"          ;; component
         "bases/sync-cli/src"]             ;; base (CLI 入口)
 :tasks {...}}
```

命名空间约定：`<project>.<component>.interface` / `<project>.<base>.core`

---

## 常见坑

### 1. 不要加不必要的 :deps

```clojure
;; ❌ 错误 — cheshire 已内置，加了会触发 Maven 下载
{:deps {cheshire/cheshire {:mvn/version "5.13.0"}}
 :tasks {...}}

;; ✅ 正确 — 直接 require
{:tasks
 {:requires ([cheshire.core :as json])
  my-task {:task (println (json/generate-string {:a 1}))}}}
```

### 2. shell vs process

```clojure
;; shell — 简单执行，继承 stdin/stdout，异常时抛出
(shell "git" "status")
(shell {:dir "/tmp"} "ls" "-la")
(shell {:out :string} "git" "rev-parse" "HEAD")  ;; 捕获输出

;; process — 更底层，返回 Process 对象
(def p (process ["git" "log"] {:out :string}))
(:out @p)  ;; deref 等待完成

;; 静默执行 + 忽略错误
(shell {:out :string :err :string :continue true} "git" "status")
```

### 3. *command-line-args* 是 seq of string

```clojure
;; bb my-task foo bar 42
;; *command-line-args* => ("foo" "bar" "42")

;; 传给 shell
(apply shell "cmd" *command-line-args*)

;; 解析数字
(parse-long (first *command-line-args*))  ;; bb 内置 parse-long

;; 转 keyword
(keyword (first *command-line-args*))
```

### 4. bb 内置 parse-long / parse-double

不需要 `Integer/parseInt`，直接用 `(parse-long "42")`。

### 5. 环境变量

```clojure
(System/getenv "HOME")           ;; 读
(shell {:extra-env {"FOO" "1"}}  ;; 传给子进程
       "my-cmd")
```

---

## 快速模板

### 最小 bb.edn

```clojure
{:tasks
 {hello {:doc "Hello world"
         :task (println "Hello" (first *command-line-args*))}}}
```

### Polylith 项目 bb.edn

```clojure
{:paths ["components/xxx/src"
         "bases/yyy/src"]
 :tasks
 {:requires ([my.yyy.core :as cli])
  cmd1 {:doc "..." :task (cli/cmd1 *command-line-args*)}
  cmd2 {:doc "..." :task (cli/cmd2 *command-line-args*)}}}
```

### 全局透传 ~/bb.edn

```clojure
{:tasks
 {proj {:doc "转发到 ~/my-project"
        :task (let [home (System/getenv "HOME")]
                (apply shell {:dir (str home "/my-project")}
                       "bb" *command-line-args*))}}}
```
