# Second Slice Verification Matrix

## 目标

- 将第二切片验证从“已有守卫集合”收敛为“统一 prepared gate”

## A. 必须通过（Prepared Gate）

1. `make verify.architecture.final_slice_readiness_audit`
2. `make verify.product.project_dashboard_baseline DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
3. `make verify.product.project_execution_consistency_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
4. `make verify.product.project_execution_pilot_precheck_guard DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## B. 已覆盖内容

- `project.initiation -> project.dashboard`
- `project.dashboard -> project.plan_bootstrap`
- `project.plan_bootstrap -> project.execution`
- `project.execution.advance`
- execution state transition
- execution entry/block/action contract
- `project_id` 上下文连续链

## C. 当前未覆盖

- 第二切片浏览器级 smoke
- 成本/合同/结算扩展链
- 非第二切片 UI 展示回归

## 统一入口

- `make verify.release.second_slice_prepared ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## 规则

- 任一 Prepared Gate 失败，则第二切片不得进入冻结结论。
- 未补浏览器证据前，不得宣称“正式冻结发布”。
