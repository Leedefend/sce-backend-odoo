---
name: verify-and-gate
description: 统一改动后的验证与门禁结论输出，优先 restricted，再按需升级到 strict/live。
metadata:
  short-description: 验证门禁统一流程（执行强化版）
---

# Verify And Gate

## Validation Strategy（强制顺序）

1. 先执行 restricted 主线验证（最小闭环）。
2. 判定是否涉及关键链路：
   - 启动链（login / system.init / ui.contract）
   - contract/schema
   - default_route / scene 路由
3. 若涉及 → 升级验证：strict / live runner。
4. 审计线独立执行（B线），不得与实现混改。
5. 三层验证必须分别出结论（禁止合并判断）。

---

## Validation Layers（必须拆分）

### 1. Code Layer（代码层）

- 是否实现目标逻辑
- 是否存在运行错误
- 是否符合模块边界

### 2. Contract Layer（契约层）

- schema 是否匹配
- 字段是否完整（无前端补语义）
- contract_version 是否正确

### 3. Gate Layer（门禁层）

- verify / guard / snapshot 是否通过
- 是否满足发布标准

👉 三层必须独立结论，不允许“整体通过”模糊描述

---

## Execution（标准命令顺序）

```bash
# 1. restricted 基线
make verify.restricted

# 2. 契约快照
make codex.snapshot.export

# 3. 架构/边界守卫
make verify.backend.guard

# 4. 前端（如涉及）
make verify.portal.smoke

# 5. 必要时升级
make verify.strict
make verify.live
```

---

## Required Result Sections（必须输出）

### 1. Code Result

- PASS / FAIL
- 失败点（文件/模块）

### 2. Contract Result

- PASS / FAIL
- 不匹配字段 / schema 差异

### 3. Environment Result

- 是否可信（trusted / conditional / invalid）
- 是否存在：
  - 缓存污染
  - DB 状态异常
  - 容器/依赖问题

### 4. Gate Result

- verify：PASS / FAIL
- snapshot：PASS / FAIL
- guard：PASS / FAIL

---

## Minimum Evidence（必须附带）

- 执行命令（完整）
- 核心日志路径（artifacts/*）
- contract snapshot 路径
- guard 执行记录
- 前端 smoke 结果（如涉及）
- trace_id（关键失败必须有）

## Failure Classification（必须归因）

- CODE_ERROR：实现逻辑错误
- CONTRACT_MISMATCH：schema/字段不匹配
- CONTRACT_MISSING：后端未提供语义
- ENV_UNSTABLE：环境不可信
- GUARD_FAIL：架构/边界违规
- SNAPSHOT_DIFF：契约快照不一致

## Decision Matrix（判定规则）

| Code | Contract | Gate | 结论 |
| ---- | -------- | ---- | ---- |
| PASS | PASS | PASS | ✅ 可进入下一批 |
| PASS | FAIL | - | ❌ 阻断（契约问题） |
| FAIL | - | - | ❌ 阻断（代码问题） |
| PASS | PASS | FAIL | ❌ 阻断（门禁问题） |
| PASS | PASS | PASS（环境不可信） | ⚠️ conditional |

## Environment Trust Rules

- 若存在以下情况 → 标记为 `conditional`：
  - 未重启服务即验证
  - 未执行 `-u` 升级模块
  - DB 状态不确定
- 若环境异常 → 禁止修复代码（先修环境）

## Rollback Trigger（触发回滚）

- contract snapshot 不可解释变化
- guard 出现架构违规
- 启动链验证失败
- default_route 错误

## Hard Constraints

- 不允许跳过 restricted 直接跑 strict/live。
- 不允许混合输出三层结论。
- 不允许在验证阶段顺手修代码（必须新批次）。
- 不允许忽略 snapshot 差异。
- 不允许无证据输出结论。

## Anti-Patterns（禁止）

- “基本通过”
- “可能是环境问题”但未标注
- 不区分 contract 与 frontend 问题
- 未跑 snapshot 就说契约正确
- 修改代码掩盖验证失败

## Batch Reminder

```text
当前批次必须明确：
- 是否涉及 contract/schema
- 是否涉及启动链
- 是否需要 strict/live 验证

否则，只允许 restricted
```
