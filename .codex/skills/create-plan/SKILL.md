---
name: create-plan
description: 在执行前生成可落地的分阶段计划，确保步骤有依赖、有验收、有回滚，直接驱动 Batch 执行。
metadata:
  short-description: 计划生成（强约束版）
---

# Create Plan (Project Standard)

## Use When
- 批次启动前需要生成执行方案（Batch-A/B/C）
- 需求不明确或存在多实现路径，需要结构化拆解
- 需要把目标转成可执行步骤与验收标准

---

## Plan Scope（必须声明）

计划必须明确：

- 目标（唯一核心目标）
- 范围（允许修改的模块/层）
- 不做（明确排除项）
- 所属批次（Batch-X）

缺失任一项 → 禁止生成计划

---

## Plan Structure（强制结构）

### 1️⃣ 目标与边界
- 本批次唯一目标
- 涉及模块/层（backend / frontend / contract / verify）
- 明确“不做”

---

### 2️⃣ 实施步骤（最小增量）
每一步必须满足：

- 单一职责（只做一件事）
- 明确依赖（必须依赖前一步）
- 不跨层（禁止 backend + UI 混做）

每步必须包含：

- 操作内容
- 修改范围
- 输出产物

---

### 3️⃣ 完成判据（必须）
每一步必须定义：

- 如何判断完成（明确条件）
- 是否可进入下一步

---

### 4️⃣ 验证步骤（强制）
必须包含：

- verify（restricted）
- contract snapshot（如涉及）
- guard（role / version / contract）
- 前端 smoke（如涉及）

---

### 5️⃣ 风险与回滚
必须包含：

- 每一步的潜在风险
- 对应回滚方式（文件/模块级别）

---

### 6️⃣ 停机条件（必须定义）
出现以下情况必须停止执行：

- 关键语义未定义（role / compat / route）
- 验证失败
- 出现跨范围需求
- 契约结构不稳定

---

## Hard Rules（必须执行）

- 一次计划只服务一个 Batch
- 禁止跨批次设计
- 禁止跨层实现（backend / frontend / contract）
- 未完成当前步骤验证，禁止进入下一步
- 契约优先于实现
- 计划必须能直接驱动 batch-execution

---

## Forbidden Actions（禁止）

- 生成“泛计划”（无步骤/无判据）
- 步骤无依赖关系
- 未定义验证就推进
- 在计划中引入未来批次内容

---

## Output Template（强制输出格式）

### 批次信息
- 批次：Batch-X
- 目标：
- 范围：
- 不做：

---

### 实施步骤

#### Step 1
- 操作：
- 修改范围：
- 输出：

完成判据：
- ...

---

#### Step 2
- 操作：
- 修改范围：
- 输出：

完成判据：
- ...

---

### 验证步骤
- verify：
- snapshot：
- guard：
- smoke：

---

### 风险与回滚
- 风险：
- 回滚：

---

### 停机条件
- ...
