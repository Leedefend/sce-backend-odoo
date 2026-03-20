---
name: project-governance-codex
description: 项目总控治理技能。用于任何实现任务前的边界确认、批次约束、验证门禁与文档同步。
metadata:
  short-description: 项目级不变原则总控（执行强化版）
---

# Project Governance Codex

## Collaboration Mechanism v2 (Enforced)

### Fixed Roles（强约束）

- Owner：唯一决策源（目标/范围/语义拍板）
- Architect Commander：唯一调度与边界控制（是否允许开工/继续/收口）
- Codex A-线（实现）：
  - 只实现执行单
  - 禁止重设计/扩展/解释
- Codex B-线（审计）：
  - 只验证与归因
  - 禁止修改代码

👉 任一角色越界 = 本批次判定无效

---

## Core Principles（不可违反）

1. 单批次单目标（Single Objective Only）
2. 不跨层（Layer Isolation）
3. 不跨批（Batch Isolation）
4. 契约优先（Contract First）
5. 语义先拍板（Semantic Freeze Before Code）
6. 验证独立（Code ≠ Contract ≠ Gate）

---

## Execution Pipeline（唯一合法路径）

```text
Batch Input
→ 边界判定（Architect）
→ 执行单（Architect）
→ A线实现
→ B线审计
→ Gate 验证（独立）
→ 收口决策（Architect）
```

任何跳步 = 违规

---

## Project Hard Constraints（系统级红线）

- 启动链不可破坏：
  `login → system.init → ui.contract`
- role 真源唯一：
  `role_surface.role_code`
- default_route 必须来自后端 contract
- public intent：
  - 禁止 rename
  - 禁止语义漂移
- compat 生命周期必须完整：
  - introduce → observe → default → deprecate → remove
- contract_version：
  - 统一语义化版本
  - 不允许隐式升级

### Create/Edit 语义红线（新增）

- 记录态判定必须基于真实主键：仅正整数 `id/res_id` 视为编辑态。
- 下列值必须视为创建态：`new` / `0` / `false` / `null` / `none` / 空值。
- `project.project` 只要契约包含 `form` 视图（含 `tree,form`）即触发表单治理。
- 系统生成字段（如 `project_code` / `code`）在创建态必须不可见，仅允许 `edit/readonly` 可见。
- 禁止以前端条件渲染替代后端契约语义；必须在治理层修复。

---

## Batch Control（批次控制机制）

### Batch 必须包含

```text
目标：唯一核心目标
范围：允许修改模块
不做：明确禁止项
```

### 自动中止条件

- 出现第二目标
- 修改未声明模块
- 触达启动链但未声明
- contract/schema 改动未声明
- 语义未拍板

---

## Execution Order（强制顺序）

1. 定义 contract / schema
2. 更新后端实现（model/service）
3. 更新接口（intent/controller）
4. 更新前端消费（如在范围内）
5. 验证
6. 文档 & snapshot

---

## Gate System（门禁体系）

### 必过门禁（按需选择）

```bash
make verify.restricted
make verify.contract.snapshot
make verify.backend.guard
make verify.portal.smoke
```

### 判定规则

| 维度 | 判定 |
| -- | -- |
| 代码 | 是否实现目标 |
| 契约 | 是否符合 schema |
| 门禁 | 是否通过验证 |
| 行为 | 是否符合启动链与路由语义 |

👉 任一失败 = 批次失败

---

## Output Contract（每批次必须产出）

### 1. 决策边界

- 做什么
- 不做什么
- 为什么现在做

### 2. 执行单

- 修改点
- 影响模块
- 禁止修改项

### 3. 验证结果（分层）

- Code：通过/失败
- Contract：通过/失败
- Gate：通过/失败

### 4. 风险与回滚

- 风险点
- 回滚路径（commit / snapshot / config）

### 5. 产物

- snapshot 路径
- logs
- docs 更新

---

## Observability（必须具备）

- 每个关键请求必须可追踪：
  - trace_id
  - intent
  - latency
- contract 必须可 snapshot
- compat 必须可观测（日志/开关）

---

## Anti-Patterns（严禁）

- 一次改：contract + 启动链 + UI
- 前端补语义
- contract 未定义直接编码
- 未验证直接进入下一批
- 审计与实现混角色
- 用“感觉正确”替代验证
- 修改 public intent 规避问题

---

## Required References（必须遵守）
- `docs/ops/codex_execution_allowlist.md`
- `docs/ops/codex_workspace_execution_rules.md`
- `ARCHITECTURE_GUARD.md`
- `docs/architecture/ai_development_guard.md`

---

## Batch Input Template（强制）

```text
启动 Batch-X

Layer Target：
Module：
Reason：

目标：
范围：
不做：
```

---

## Final Authority Rule（最终裁决）

- 是否开工：Architect
- 是否通过：Gate + Architect
- 是否进入下一批：Architect
- 是否重构：必须新批次

👉 没有“边做边想”，只有“先定再做”
