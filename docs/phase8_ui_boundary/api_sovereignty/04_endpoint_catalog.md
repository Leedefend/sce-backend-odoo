# Endpoint Catalog（五中心端点目录）

**版本**：v1.0  
**说明**：只定义目录，不实现代码。用于后续 Phase8-B/Phase9 的开发输入。

---

## A) 项目中心（Project Center）

### 项目
- `GET /api/v1/projects`（project_read）
- `GET /api/v1/projects/{id}`（project_read）
- `POST /api/v1/projects`（project_user）
- `PATCH /api/v1/projects/{id}`（project_user）

### WBS/结构/清单（示例）
- `GET /api/v1/projects/{id}/structure`（project_read）
- `GET /api/v1/projects/{id}/boq_lines`（project_read）
- `POST /api/v1/projects/{id}/boq_imports`（project_user）— 导入触发（后端异步可选）

---

## B) 成控中心（Cost Center）

### 项目预算
- `GET /api/v1/budgets`（cost_read）
- `GET /api/v1/budgets/{id}`（cost_read）
- `POST /api/v1/budgets`（cost_user）
- `PATCH /api/v1/budgets/{id}`（cost_user）

### 成本对比/分析（Level 3 候选）
- `GET /api/v1/cost/compare`（cost_manager 或 cost_user + scope）  
> 未来驾驶舱/经营分析必须 API-first（白皮书 Level 3）

---

## C) 合同中心（Contract Center）

### 合同台账
- `GET /api/v1/contracts`（contract_read）
- `GET /api/v1/contracts/{id}`（contract_read）
- `POST /api/v1/contracts`（contract_user）
- `PATCH /api/v1/contracts/{id}`（contract_user）

---

## D) 物资中心（Material Center）

### 物资计划
- `GET /api/v1/material_plans`（material_read）
- `GET /api/v1/material_plans/{id}`（material_read）
- `POST /api/v1/material_plans`（material_user）
- `PATCH /api/v1/material_plans/{id}`（material_user）
- Actions:
  - `POST /api/v1/material_plans/{id}/actions/submit`（material_user）
  - `POST /api/v1/material_plans/{id}/actions/approve`（material_manager）

---

## E) 财务中心（Finance Center）

### 结算单
- `GET /api/v1/settlements`（finance_read）
- `GET /api/v1/settlements/{id}`（finance_read）
- `POST /api/v1/settlements`（finance_user）
- Actions:
  - `POST /api/v1/settlements/{id}/actions/approve`（finance_manager）

### 付款申请
- `GET /api/v1/payment_requests`（finance_read）
- `GET /api/v1/payment_requests/{id}`（finance_read）
- `POST /api/v1/payment_requests`（finance_user）
- Actions:
  - `POST /api/v1/payment_requests/{id}/actions/submit`（finance_user）
  - `POST /api/v1/payment_requests/{id}/actions/approve`（finance_manager）

---

## F) 平台级（Level 0/1）

### 字典/配置（管理型）
- `GET /api/v1/dictionaries`（admin 或 对应 capability_read）
- `POST /api/v1/dictionaries`（admin/manager）

> 这类接口属于“管理后台能力”，可继续用 Odoo UI，但必须可被 API 操作替换。
