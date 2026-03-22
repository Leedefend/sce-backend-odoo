# Product Baseline · `project.initiation` v1

## Layer Target
- `Scene Layer`
- `Page Orchestration Layer`
- `Domain/Product Handler Layer`

## Module
- `addons/smart_construction_scene`
- `addons/smart_construction_core`
- `scripts/verify/product_project_initiation_smoke.py`

## Reason
- 冻结第一产品场景的可执行闭环：`scene -> contract -> intent -> handler -> record -> contract return`。

## Baseline Intent Chain
1. `login`
2. `system.init`
3. `app.open`（project app）
4. `project.initiation.enter`
5. `project.dashboard.open`（由 `suggested_action_payload` 指引）
6. `ui.contract`（由 `contract_ref` 指引）

## Role Matrix（冻结）
- `owner`: 可登录/可初始化/可打开场景；创建默认应被拒绝（contract-safe，不得 500）
- `pm`: 可登录/可初始化/可打开场景；创建应通过并返回 suggested_action + contract_ref
- `finance`: 可登录/可初始化/可打开场景；创建默认应被拒绝（contract-safe，不得 500）
- `executive`: 可登录/可初始化/可打开场景；创建应通过并返回 suggested_action + contract_ref

对应验证：`make verify.product.project_initiation.roles`

## ContractRef Shape（冻结）
- 一级标准：
  - `contract_ref.intent = ui.contract`
  - `contract_ref.params = { op: menu, menu_id/menu_xmlid }`
- 二级降级（仅一级不可用时）：
  - `contract_ref.params = { op: model, model }`
- 当 `suggested_action_payload.intent = ui.contract` 时，必须与 `contract_ref` 入口一致。
- 当 `suggested_action_payload.intent` 指向产品动作（如 `project.dashboard.open`）时，必须保证能收敛到可执行 `contract_ref`。

## Suggested Action Shape（冻结）
- `suggested_action_payload.intent`：必填
- `suggested_action_payload.params`：必填
- `suggested_action_payload.reason_code`：必填（可由 `params.reason_code` 冗余承载）
- 当前 `project.initiation.enter` 成功后约定：
  - `intent = project.dashboard.open`
  - `params.project_id` 与创建记录 `record.id` 连续一致

对应验证：`make verify.product.contract_ref_shape_guard`

## Minimum Acceptance
- 创建返回 `state=ready|success`
- 返回有效 `record.id`
- 返回非空 `suggested_action`
- 返回可执行 `contract_ref`
- contract 返回非空（禁止 fallback-only 空壳）
- 角色矩阵行为满足冻结预期（允许/拒绝）
- `contract_ref` shape 满足 menu-first 冻结规范
- `project.initiation -> project.dashboard` 链路打通
- `suggested_action` shape 满足 intent/params/reason_code 冻结规范
- `project_id` 在场景链路中连续（initiation -> suggested_action -> dashboard.open -> contract_ref）

## Verify Command
- `make verify.product.project_initiation DB_NAME=<db> E2E_LOGIN=<login> E2E_PASSWORD=<password>`
- `make verify.product.project_initiation.roles DB_NAME=<db> ...`
- `make verify.product.contract_ref_shape_guard DB_NAME=<db> ...`
- `make verify.product.project_initiation.full DB_NAME=<db> ...`
- `make verify.product.project_flow.initiation_dashboard DB_NAME=<db> ...`
- `make verify.product.suggested_action_shape_guard DB_NAME=<db> ...`
- `make verify.product.project_context_chain_guard DB_NAME=<db> ...`
- `make verify.product.project_dashboard_non_empty_guard DB_NAME=<db> ...`
- `make verify.product.phase12c DB_NAME=<db> ...`

## Evidence
- Artifact: `artifacts/backend/product_project_initiation_smoke.json`
- Artifact: `artifacts/backend/product_project_initiation_roles_smoke.json`
- Artifact: `artifacts/backend/product_contract_ref_shape_guard.json`
- Artifact: `artifacts/backend/product_project_flow_initiation_dashboard_smoke.json`
- Artifact: `artifacts/backend/product_suggested_action_shape_guard.json`
- Artifact: `artifacts/backend/product_project_context_chain_guard.json`
- Artifact: `artifacts/backend/product_project_dashboard_non_empty_guard.json`
- Iteration log: `docs/ops/iterations/delivery_context_switch_log_v1.md`
