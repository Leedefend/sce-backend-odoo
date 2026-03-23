# First Release Slice Freeze Report

## 1. 产品口径

- 冻结产品：`施工企业项目管理系统（首发版）`
- 冻结切片：`项目创建 -> 驾驶舱`
- 口径文档：
  - `docs/ops/releases/first_release_product_contract.md`

## 2. 五层映射

- L1：`project.project`
- L2：`create_project / initialize_project`
- L3：`project.initiation / project.dashboard`
- L4：创建输入/输出、dashboard entry/block contract
- L5：创建页 / 驾驶舱页

冻结文档：
- `docs/architecture/first_release_slice_five_layer_freeze.md`

## 3. Dashboard Block 白名单

- 固定白名单：
  - `progress`
  - `risks`
  - `next_actions`

冻结文档：
- `docs/product/dashboard_block_whitelist.md`

## 4. Contract 范围

- 创建输入 contract
- 创建输出 contract
- dashboard entry contract
- dashboard block contract

审计文档：
- `docs/audit/first_slice_contract_guard_audit.md`

## 5. 验证矩阵

- Release Gate 已冻结：
  - `final_slice_readiness_audit`
  - `project_creation_mainline_guard`
  - `dashboard_entry_contract_guard`
  - `dashboard_block_contract_guard`
  - `project_flow.initiation_dashboard`
  - `browser smoke`

矩阵文档：
- `docs/ops/releases/first_release_verification_matrix.md`

## 6. 前端边界状态

- 首发链前端已满足冻结要求
- 驾驶舱页已转为 contract-first 消费
- 剩余仅 `P2` 通用展示 fallback

文档：
- `docs/audit/first_slice_frontend_boundary_lock.md`

## 7. 已接受残留（P2）

- 驾驶舱页通用展示 fallback
- 不影响首发链 contract 语义
- 不阻断发布

## 8. 明确排除项

- 成本闭环
- 合同付款
- 结算分析
- ActionView Batch-C
- 非首发链路改动

## 9. 冻结验证结果

### Release Gate

- `make verify.release.first_slice_freeze ENV=test ENV_FILE=.env.prod.sim COMPOSE_PROJECT_NAME=sc-backend-odoo-prod-sim PROJECT=sc-backend-odoo-prod-sim BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
- 结果：`PASS`

### 关键证据

- `artifacts/backend/final_slice_readiness_audit.json`
- `artifacts/backend/product_project_creation_mainline_guard.json`
- `artifacts/backend/product_project_dashboard_entry_contract_guard.json`
- `artifacts/backend/product_project_dashboard_block_contract_guard.json`
- `artifacts/backend/product_project_flow_initiation_dashboard_smoke.json`
- `artifacts/codex/first-release-slice-browser-smoke/20260323T051219Z/summary.json`

## 冻结结论

- `项目创建 -> 驾驶舱` 已形成首发切片唯一基线。
- 本文是首发切片冻结的权威收口文档。
- 后续任何首发发布、演示、销售、交付口径，必须与本文一致。
- 当前冻结判定：`可发布切片`
