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
5. `ui.contract`（由 `contract_ref` / `suggested_action_payload` 指引）

## Minimum Acceptance
- 创建返回 `state=ready|success`
- 返回有效 `record.id`
- 返回非空 `suggested_action`
- 返回可执行 `contract_ref`
- contract 返回非空（禁止 fallback-only 空壳）

## Verify Command
- `make verify.product.project_initiation DB_NAME=<db> E2E_LOGIN=<login> E2E_PASSWORD=<password>`

## Evidence
- Artifact: `artifacts/backend/product_project_initiation_smoke.json`
- Iteration log: `docs/ops/iterations/delivery_context_switch_log_v1.md`
