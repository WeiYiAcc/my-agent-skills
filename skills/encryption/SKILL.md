---
name: encryption
description: 文件加密操作。涵盖 chezmoi age（dotfiles 加密）和 sops + age（项目仓库加密）。当用户需要加密、解密、编辑加密文件，或新增敏感文件到 dotfiles/ariadne 仓库时使用。
---

# 文件加密

两层加密体系，共用同一个 age key：`~/.config/chezmoi/key.txt`

## ⚠️ 解密纪律（AI 必读,最高优先级）

**本 session 反复泄露密钥的根因固化于此。任何解密操作前必读。**

### 核心铁律:密钥值永不进入 transcript

解密后的明文密钥值,**永远不能**出现在任何会被记录的输出里——不 `cat`/`head`/`print`/
`display`/`echo`,不管它是从文件读来的、还是脚本自己拼出来的。违反=密钥泄露=必须轮换。

### 两类必须区分的泄露面

1. **read-on-decrypt**:`sops decrypt file | head`、`chezmoi cat ~/.env`、`git show ...age`
   后直接看——读原始文件时泄露。
2. **build-on-construct**:自己用 Python 把密钥拼进 dict/yaml 字符串,然后 `print(那个变量)`
   ——构建新内容时泄露。**这类最隐蔽**,容易以为"我只是看格式对不对"。

### 安全验证模式(用这些,不要打印)

| 要验证的事 | 安全做法 | 禁止 |
|---|---|---|
| 值是否正确/一致 | 比对 `hashlib.sha256(v).hexdigest()[:12]` 或 `a == b` 返回 bool | `print(v)` |
| 值是否存在/长度 | `len(v)`、`bool(v)` | `head -c N`（仍打印前 N 字节!） |
| 单字段取值 | `sops decrypt --extract '["grp"]["key"]'` 再 pipe 给下游,不打印 | `sops decrypt` 全量 dump |
| 文件是否正确渲染 | `chezmoi execute-template` 结果算 hash 比对;`chezmoi apply` 后比 `render==disk` 的 hash | `chezmoi diff <敏感target>`（**会打印明文 diff!**） |
| key 结构(非值) | `sed -E 's/=.*/=<redacted>/'`、只打印 key 名 value 替成 `<redacted>` | 直接 dump |

### 操作载体:用 eval 内存,不用 shell

涉及密钥的多步操作一律走 `eval`(Python)——解密结果留在内存变量,只做纯内存 dict 操作、
写文件、hash/bool 校验。**绝不**把密钥值传给 `print`/`display`,**绝不**用 `subprocess`
把密钥当 argv 传(会进 `/proc/<pid>/cmdline`),要传值用 `--value-stdin`/`--value-file`/stdin pipe。

### 临时文件

密钥相关临时文件用 `mktemp` + `chmod 600`,用完立即 `shred -u`。密文备份放 `/tmp` 也要清理。
**绝不**产生明文密钥临时文件;给 sops 密文加注释直接改密文文件的注释行(MAC 不覆盖注释),
无需解密到明文。

### chezmoi diff 特别警告

`chezmoi diff` 对"渲染出敏感内容的模板 target"**会打印完整明文 diff**。验证这类 target
用 `chezmoi apply <target>` + `render==disk` 的 hash 比对,或 `chezmoi diff <target> | wc -l`
只看行数,**绝不**让 diff 内容进 transcript。

## sops 二进制的 bootstrap 依赖链（DAG）

**先澄清一个容易混淆的边界**：`chezmoi apply` 解密 `encrypted_*.age` 文件走的是
chezmoi **内建**的 age 引擎（`chezmoi.toml` 里 `encryption = "age"`，Go 原生实现，
不 shell out 到任何外部程序）——绝大多数加密文件（SSH keys、大部分 `.tmpl.age`）
完全不需要 sops 二进制存在。

**sops 真正被用到的地方只有极少数模板**：`api-keys.env.tmpl` 和 `mcp.json.tmpl`
这两个文件本身不是 chezmoi age 加密（无 `.age` 后缀），而是普通模板，内部用
`{{ output "sops" "decrypt" (joinPath .chezmoi.sourceDir "dot_pi/agent/secrets.yaml") | fromYaml }}`
这个 chezmoi 模板函数**主动 shell out** 到 sops，去解另一个独立文件——
`dot_pi/agent/secrets.yaml`，这个文件走的是 sops 自己的加密格式（YAML，key 明文
value 密文），和 chezmoi 的 age 整文件加密是完全不同的两套机制，只是共用同一把
age key。

`~/.local/bin/sops` **不是** home-manager/nix profile 装的，也不是 yadm 自身职责——是
`my-yadm-bootstrap` 仓库的 `bootstrap-local-wsl.sh` 脚本在 **Phase 2（chezmoi init 前置层）**
手动 curl 装的独立二进制，早于 home-manager 第一次 generation 存在：

```
yadm (HTTPS clone) → yadm decrypt
  → ssh key + age key（~/.config/chezmoi/key.txt）+ chezmoi.toml 就位
  → [Phase 2] curl 装 chezmoi 二进制
  → [Phase 2] curl 装 sops 二进制 ← api-keys.env.tmpl / mcp.json.tmpl
    渲染时需要它，此时还没有 home-manager，不能等 nix 装
  → ~/.config/sops/age/keys.txt symlink 到 age key
  → chezmoi apply（触发 nix 安装 + home-manager switch，nix profile 里
    可能再装一份 sops，但 PATH 优先级下 ~/.local/bin 这份才是实际生效的）
```

**为什么提前装**：即便只有 2 个模板依赖 sops，缺了它这 2 个模板会渲染失败——
`chezmoi apply` 本身又是触发 home-manager switch 的入口，若指望 home-manager
装好 sops 再回头渲染，就是自己等自己。所以 bootstrap 脚本选择在 `chezmoi apply`
之前、用 curl 下载一份独立的 sops 二进制到 `~/.local/bin/`，避免这个先有鸡还是
先有蛋的顺序问题——**不是"chezmoi apply 整体依赖 sops"，只是这两个模板局部依赖**。

**踩坑记录（2026-07-14）**：`home-manager switch` 补跑一次 9 天积压的改动后，
`nix store diff-closures` 显示 home-manager profile 里的 sops 包被移除
（`home.packages` 里 7-11 起停用了它，因为不再需要 nix 管的那份）。一度误以为
sops 功能会失效，实测 `which sops` 依然命中 `~/.local/bin/sops`（bootstrap 阶段装的
那份，不受 home-manager 影响），`chezmoi cat`/`chezmoi diff` 全链路正常——**home-manager
的 sops 包和 bootstrap 装的 sops 二进制是两份独立存在，互不依赖，砍掉 nix 那份不影响
chezmoi 的加解密能力**。

## 判断用哪个（决策树）

```
文件本身就是 .yaml/.yml？
  → sops + age(逐值加密,key/注释明文可见)  [层级 2]

多个密钥聚在一起 / 需要注释说明 / 未来 CI 可能单独取某字段 / .env / 多 provider JSON？
  → 不单独加密!统一从 dot_pi/agent/secrets.yaml 用 chezmoi 模板生成  [层级 0,首选]
    (secrets.yaml 是唯一真相源,消费方写 *.tmpl 引用它)

单一密钥 / 证书 / 二进制内容(SSH key、*.pem、atuin key、syncthing cert)？
  → chezmoi age(整文件加密)  [层级 1]

整份内容想保密的非结构化文件(私有 skill 的 md/py/json)？
  → chezmoi age(整文件加密)  [层级 1]

临时/一次性？
  → age 命令行  [层级 3]
```

**核心政策(2026-07-14 确立)**:除 `.yaml`/`.yml` 本身外,所有多值/需注释/CI 消费的密钥
文件(`.env`、多 provider `creds.json` 等)**统一从 `dot_pi/agent/secrets.yaml` 生成**,
不再各自独立 `.age` 加密。理由:唯一真相源消除"密钥散落多个 .age、AI/人搞错在哪个文件"
的位置错乱风险(本 session 反复泄露的深层诱因之一);key 名明文可见+注释说明用途,不解密
就能看懂结构;CI 可 `sops decrypt --extract` 取单字段。

## 层级 0：secrets.yaml 模板生成（首选,多值密钥）

`dot_pi/agent/secrets.yaml`(sops+age 加密)是所有多值密钥的唯一真相源。消费方是 chezmoi
模板文件(`*.tmpl`),渲染时 shell out 到 sops 解密并取值。

### secrets.yaml 分组结构

按用途分组,每组带注释。**非敏感值**(URL、用户名、公开常量)用 `_unencrypted` 后缀标记、
和敏感值同组存放(约定见现有 `ariadne_fact.ARIADNE_FACT_URL_unencrypted`),明文便于不解密查看。

### 加/改字段(逐 key,不解密全文)

```bash
# 加/改单个字段:值走 stdin,不进 argv/transcript
printf '%s' "$VALUE" | sops set --value-stdin dot_pi/agent/secrets.yaml '["分组"]["KEY"]'
# AI 用 eval:subprocess.run(["sops","set","--value-stdin",f,idx], input=json.dumps(v))
```

### 加注释(直接改密文,MAC 不覆盖注释行)

```bash
# 密文文件里 # 注释行是明文,直接编辑注释不破坏解密,零明文落盘
# 交互编辑整体:sops dot_pi/agent/secrets.yaml
```

### 新增一个消费方(把某密钥文件从 .age 迁到模板)

```
1. sops set 把值写入 secrets.yaml 对应分组(见上)
2. 写 <target>.tmpl:开头 {{- $secrets := output "sops" "decrypt" (joinPath .chezmoi.sourceDir "dot_pi/agent/secrets.yaml") | fromYaml -}}
   取值 {{ (index $secrets "分组").KEY }}
3. chezmoi execute-template 渲染,hash 比对旧 .age 解密内容确认一致(不打印!)
4. rm 旧 encrypted_*.age(clean cutover,不留死文件)
5. chezmoi apply <target>,比 render==disk 的 hash
```

现有消费方模板:`dot_config/exact_secrets/api-keys.env.tmpl`、`dot_pi/agent/mcp.json.tmpl`、
`exact_dnscontrol/creds.json.tmpl`、`private_dot_hermes/dot_env.tmpl`、
`exact_sub2api-deploy/dot_env.tmpl`(仅密钥走模板,200+行非敏感配置留明文)。

## 层级 1：chezmoi age（dotfiles）

用于 `~/.local/share/chezmoi/` 管理的所有敏感文件。

### 新增加密文件
```bash
chezmoi add --encrypt ~/path/to/secret-file
```
源文件自动变为 `encrypted_xxx.age`，`chezmoi apply` 时自动解密。

### 编辑已加密文件
```bash
chezmoi edit ~/path/to/secret-file
```

### 部署（解密到目标路径）
```bash
chezmoi apply
```

### 查看加密文件内容（不修改）
```bash
chezmoi cat ~/path/to/secret-file
```

### 提交变更（repo 用 jj）
```bash
cd ~/.local/share/chezmoi
jj commit -m "chore: update encrypted xxx"
jj bookmark set master -r @-
jj git push --bookmark master
git checkout master
```

### 当前加密文件清单
- **secrets.yaml 生成(层级 0)**: `~/dnscontrol/creds.json`, `~/sub2api-deploy/.env`(仅密钥),
  `~/.hermes/.env`, `~/.config/secrets/api-keys.env`, `~/.pi/agent/mcp.json`
  → 改这些改 `dot_pi/agent/secrets.yaml`,不是改 target
- SSH keys(层级 1 age): `~/.ssh/id_rsa, config, *.pem`
- 单值/证书(层级 1 age): `~/.local/share/atuin/key`, `~/.local/state/syncthing/*.pem`,
  `~/.config/restic/password`, `~/.config/rclone/rclone.conf`
- 待迁移到层级 0(仍是 age,后续按政策转 secrets.yaml): `~/cloudflare/credentials.env`
- 其他单值(层级 1 age): `~/key/discord_backup_codes`

## 层级 2：sops + age（项目仓库）

用于 ariadne 等 jj 管理的仓库中的敏感文件。不能用 git-crypt（jj 不触发 git filter）。

### 环境变量
```bash
export SOPS_AGE_KEY_FILE=~/.config/chezmoi/key.txt
```

### 配置（仓库根目录 `.sops.yaml`）
```yaml
creation_rules:
  - path_regex: path/to/secrets/.*\.json$
    age: age10ue93j9ud8kepwyaldd6c8e5g0sk0jf4lfkaz9aqv0gxqyvzjusq5f8pyt
```

### 加密新文件
```bash
sops encrypt --in-place file.json
```

### 解密查看
```bash
sops decrypt file.json          # 输出到 stdout
sops decrypt -i file.json       # 原地解密（⚠️ 小心别提交明文）
```

### 编辑（推荐方式）
```bash
sops file.json
# 自动：解密 → 打开 $EDITOR → 保存后自动加密
```

### 注意事项
- sops **不支持** JSON 数组 `[...]` 作为顶层，必须是 `{}` 对象
- `.sops.yaml` 的 `path_regex` 基于仓库根目录的相对路径
- `.env` 等非结构化文件会全文加密（注释也加密），diff 可读性不如 JSON/YAML
- 加密后文件名不变，内容变为密文，JSON key 可见、value 加密

### 当前 sops 配置
- 仓库：`~/ghq/github.com/WeiYiAcc/ariadne-fact/`
- 规则：`my-toolbox/my-py/projects/claude-auto-login/accounts/*.json`

## 层级 3：age 命令行（临时/一次性）

```bash
# 加密
age -r age10ue93j9ud8kepwyaldd6c8e5g0sk0jf4lfkaz9aqv0gxqyvzjusq5f8pyt -o file.age file

# 解密
age -d -i ~/.config/chezmoi/key.txt file.age > file
```

## age key 信息

- 路径: `~/.config/chezmoi/key.txt`
- recipient: `age10ue93j9ud8kepwyaldd6c8e5g0sk0jf4lfkaz9aqv0gxqyvzjusq5f8pyt`
- 用途: chezmoi age + sops + 手动 age，三者共用
