# First Release Verification Matrix

## 目标

- 将首发切片验证从“散验证”冻结为“发布门禁”

## 验证分类

### A. 必须通过（Release Gate）

1. `make verify.product.final_slice_readiness_audit`
2. `make verify.product.project_creation_mainline_guard`
3. `make verify.product.project_dashboard_entry_contract_guard DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
4. `make verify.product.project_dashboard_block_contract_guard DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
5. `make verify.product.project_flow.initiation_dashboard DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`
6. `make verify.portal.first_release_slice_browser_smoke.host BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

### B. 建议通过

1. `make verify.frontend.typecheck.strict`
2. `make verify.architecture.orchestration_platform_guard`
3. `make verify.architecture.five_layer_workspace_audit`

### C. 非首发范围

- 计划 / 执行 / 成本 / 合同付款 / 结算相关 verify
- `ActionView` 深化相关 verify
- 非首发 UI smoke

## 冻结执行顺序

1. 架构基线
   - `make verify.product.final_slice_readiness_audit`
2. 创建主链
   - `make verify.product.project_creation_mainline_guard`
3. 驾驶舱契约
   - `make verify.product.project_dashboard_entry_contract_guard ...`
   - `make verify.product.project_dashboard_block_contract_guard ...`
4. 首发链 flow
   - `make verify.product.project_flow.initiation_dashboard ...`
5. 浏览器链
   - `make verify.portal.first_release_slice_browser_smoke.host ...`

## 统一入口

- 统一 release gate 命令：
  - `make verify.release.first_slice_freeze BASE_URL=http://127.0.0.1 ARTIFACTS_DIR=artifacts DB_NAME=sc_prod_sim E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`

## 规则

- 不允许临时拼验证
- 不允许跳过失败项
- 任一 Release Gate 失败，首发切片冻结无效
