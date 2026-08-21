---
name: logseq-db-schema
description: Logseq DB 版 my-logseq-sync 图谱的 schema 速查。包含 class 定义、property ident 映射、closed-value 定义。静态数据，手动维护。关联 skill：logseq-db-api（操作方法）。
---

# Logseq DB Schema 速查（my-logseq-sync 图谱）

关联：操作方法见 `logseq-db-api` skill。

## Classes

| Class 名 | Ident | UUID | ID | Properties |
|-----------|-------|------|----|-----------|
| 跨省交通补 | `:user.class/-u0Xvj_Cl` | `6a28da23-3d4e-4d30-8d57-063693bcdfd5` | 22003 | 年度, 申请表, 务工证明, 身份证银行卡, 人工复核, 打印状态, 盖章状态 |

## Property Ident 映射

### 跨省交通补 class 的 properties

| 中文名 | Ident | 类型 | 说明 |
|--------|-------|------|------|
| 年度 | `:user.property/-xfJw4WBT` | number (closed-value) | 2026 / 2027 |
| 申请表 | `:user.property/shenqingbiao` | checkbox | |
| 务工证明 | `:user.property/wugongzhengming` | checkbox | |
| 身份证银行卡 | `:user.property/shenfenzheng-yinhangka` | checkbox | |
| 人工复核 | `:user.property/rengong-fuhe` | checkbox | |
| 打印状态 | `:user.property/-fX6MtxGp` | checkbox | |
| 盖章状态 | `:user.property/-zyHFw8P1` | checkbox | |

### 系统 properties（常用）

| 名称 | Ident | 说明 |
|------|-------|------|
| tags | `:block/tags` | 设置 class 关联（值为 class 页面名） |
| status | `:logseq.property/status` | 内置 Task status |
| priority | `:logseq.property/priority` | 内置 Task priority |

## Closed Values（年度）

| 值 | UUID |
|----|------|
| 2026 | `6a28dd51-f909-4a0e-ac2b-495ec39363a3` |
| 2027 | `6a28dd58-66dc-4379-8f59-b84c0c8925ab` |

## Property 页面识别规则

- Property 页面 UUID 以 `00000002-` 开头
- 通过 `getBlock(uuid)` 返回的 `ident` 字段获取真实 ident
- 中文 property 的 ident 通常是拼音（如 `wugongzhengming`）
- 早期创建的 property 可能是随机编码（如 `-xfJw4WBT`）

## Journal 页面名格式

```
jan 1st, 2026
feb 2nd, 2026
mar 3rd, 2026
apr 4th, 2026
jun 11th, 2026
```

小写英文月份 + 序数词日期 + 4位年份。

## 如何新增 Property 到 Schema

无法通过 HTTP API 创建新 property 定义。需要：
1. 在 Logseq UI 中手动添加 property 到 class
2. 或通过 `import-edn` 导入

添加后用以下方式查找 ident：
```bash
# getAllPages 找到 00000002- 开头的新 property 页面
# 然后 getBlock(uuid) 读取 ident 字段
```
