---
name: frontend-contract-consumer
description: 规范前端消费后端契约（schema → store → 页面），禁止语义推导，保证启动链与契约一致。
metadata:
  short-description: 前端契约消费（强约束版）
---

# Frontend Contract Consumer (Project Standard)

## Use When
- 修改 `frontend/` 中：
  - session store
  - schema / type 定义
  - 启动链（login → system.init → ui.contract）
  - 页面契约消费逻辑

---

## Consumption Scope（必须声明）

每次修改必须明确：

- 当前批次（Batch-X）
- 涉及契约（login / system.init / ui.contract）
- 影响范围（schema / store / 页面）
- 不做（禁止触达的前端模块）

---

## Consumption Order
必须按顺序执行：

1️⃣ 更新 schema / type  
2️⃣ 更新 store（状态映射与派生）  
3️⃣ 更新页面消费逻辑

禁止跳序或反向修改。

---

## Contract Mapping Rules（核心规则）

### 1️⃣ 后端契约 → 前端 schema
- 所有字段必须先定义在 schema/type 中
- 禁止页面直接访问未声明字段

---

### 2️⃣ schema → store
- store 只做映射与最小派生
- 禁止在 store 中推导业务语义

---

### 3️⃣ store → 页面
- 页面只消费 store
- 禁止页面直接依赖后端返回结构

## Hard Constraints
- 前端不得自行推导后端应提供语义。
- 兼容策略必须区分 `compat/default/debug` 三态。
- 启动链固定：`login -> system.init -> ui.contract`。
- 页面结构遵循 `native_view_reuse_frontend_spec_v1`。
- `role_surface.role_code` 为 role 唯一真源，不得前端自推导。
- `default_route` 必须以后端契约语义为准。
- 未在本批次范围内，禁止前端大改。

### 启动链约束（强制）

必须保持：

login → system.init → ui.contract

检查：

- 不允许绕过 system.init
- 不允许页面直接调用其他 intent 初始化
- 不允许隐式跳转逻辑

### 角色与权限

- `role_surface.role_code` 为唯一真源
- 禁止前端基于 groups 推导 role
- 禁止页面自行判断权限逻辑

### 路由语义

- `default_route` 必须完全以后端契约为准
- 禁止前端通过 menu/路径推导 scene

### 页面结构

- 必须遵循：`native_view_reuse_frontend_spec_v1`
- 禁止页面结构私自扩展契约字段

### 批次边界

- 未在当前 Batch 范围内：
  - 禁止前端大规模改动
  - 禁止重构页面结构
  - 禁止跨模块修改

## Compatibility Rules（兼容策略）

- default：只使用新结构
- compat：仅用于迁移，不进入主逻辑
- debug：仅用于开发调试，不参与页面渲染

## Verification（必须执行）

### 类型验证
- TypeScript / 类型检查必须通过
- schema 与后端字段一致

### 启动链验证
- login → system.init → ui.contract 正常执行
- 无绕过路径

### 行为验证
- 页面无 fallback 推导逻辑
- store 不存在隐式计算字段
- route 与后端一致

## Forbidden Actions（禁止）

- 页面直接解析后端返回
- 在 store 中推导 role / route / capability
- 使用 groups 替代 entitlement
- 混用 compat/default/debug 数据
- 未更新 schema 直接改页面
- 跨批次前端改动

## Output Template（执行输出）

### 修改内容
- schema：
- store：
- 页面：

---

### 验证结果
- 类型检查：
- 启动链：
- 页面行为：

---

### 风险
- ...

---

### 回滚
- ...
