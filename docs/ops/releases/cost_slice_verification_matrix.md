# FR-3 Cost Slice Verification Matrix

## 目标
- 将 FR-3 成本切片验证从“prepared gate”收敛为“统一 freeze gate”

## Scope
- Stage: `Freeze`
- Slice: `project creation -> dashboard -> plan -> execution -> cost record -> cost summary`
- Boundary:
  - include `cost.tracking.enter`
  - include `cost.tracking.record.create`
  - include `cost_entry / cost_list / cost_summary`
  - exclude budget / analysis / approval / contract / payment / settlement

## A. 必须通过（Freeze Gate）
1. `make verify.architecture.final_slice_readiness_audit`
2. `make verify.product.cost_entry_contract_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
3. `make verify.product.cost_list_block_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
4. `make verify.product.cost_summary_block_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
5. `make verify.product.project_flow.execution_cost DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
6. `make verify.portal.cost_slice_browser_smoke.host BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## B. 已覆盖内容
- `project.initiation -> project.dashboard`
- `project.dashboard -> project.plan_bootstrap`
- `project.plan_bootstrap -> project.execution`
- `project.execution -> cost.tracking`
- `cost.tracking.record.create`
- `cost_entry / cost_list / cost_summary`
- `project_id` 上下文连续链

## C. 当前未覆盖
- 成本预算/分析/审批扩展链
- 合同/付款/结算扩展链
- 非第三切片 UI 展示回归

## 统一入口
- `make verify.release.cost_slice_freeze ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## 规则
- 任一 Freeze Gate 失败，则 FR-3 冻结无效。
