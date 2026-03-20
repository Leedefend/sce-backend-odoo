---
name: contract-audit
description: 审计 intent 返回结构是否符合项目契约收口规范（login/system.init/ui.contract），输出可执行审计结论。
metadata:
  short-description: 契约审计（强约束版）
---

# Contract Audit (Project Standard)

## Use When
- 审计 `login` / `system.init` / `ui.contract` 等主链 intent 返回
- 批次验收（Batch-A/B/C）前的契约达标判断
- contract snapshot / verify / guard 前置检查

## Audit Scope（必须覆盖）
以下维度必须逐条检查：

### 1️⃣ 顶层结构
- 是否符合统一结构（data / meta / errors / debug）
- 是否存在历史残留字段（如 system/intents/groups 泄漏）

### 2️⃣ Contract Version
- `meta.contract_version` 与 `schema_version` 是否语义化一致
- 是否存在 `v0.x / v1` 混用

### 3️⃣ 模式边界（关键）
- default / compat / debug 是否严格隔离
- default 模式禁止：
  - groups
  - intents
  - 调试字段
- compat 仅允许最小兼容字段
- debug 必须集中在 `debug` 节点

### 4️⃣ 启动链约束（强制）
必须满足：

login → system.init → ui.contract

检查：
- 是否存在 `bootstrap.next_intent`
- 是否允许绕过 init
- 是否存在非法入口

### 5️⃣ 权限与角色
- 是否使用 `entitlement` 而不是直接暴露 groups
- role 是否来自单一来源（不得多源推导）

### 6️⃣ 前端消费影响
- 是否破坏 session store
- 是否破坏启动链
- 是否需要 schema 适配

### 7️⃣ 验证与证据
- 是否具备：
  - contract snapshot
  - verify 结果
  - guard 检查

### 8️⃣ 创建态字段治理（强制）
- 系统生成字段（如 `project_code` / `code`）必须由后端契约控制，创建态不可见。
- 必须核对 `render_profile` 语义：`new/0/null/none/false` 不得判定为编辑态。
- 若存在 `tree,form` 等复合视图，仍需触发表单治理并执行创建态隐藏规则。

## Hard Rules（必须执行）
- 禁止凭感觉评价，必须逐条对照收口计划。
- 仅按当前批次目标审计，禁止讨论下一批实现。
- 审计线禁止改代码。
- 发现阻塞项必须给出：
  - 影响范围（前端 / 后端 / 启动链）
  - 是否需要回滚

## Severity 定义（必须使用）

- S0（阻塞）：破坏启动链 / 契约主结构 / 前端无法运行
- S1（严重）：违背契约规范但可运行（如 groups 泄漏）
- S2（建议）：结构优化或未来风险

## Output Template（强制格式）

结论：通过 / 不通过

达标项：
- ...

未达项：
- [S1][字段路径] 问题描述 → 影响

阻塞项：
- [S0][字段路径] 问题描述  
  影响：  
  建议：

建议项：
- [S2] ...

## Audit Input Templates
```text
这是 Batch-X 的实现代码

要求：
- 只按本批次目标审计
- 输出达标/未达/阻塞/建议
```

```text
这是 Batch-X 的实际返回

要求：
- 只判断是否达标
- 不讨论下一批
```
