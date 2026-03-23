# Settlement Slice Verification Matrix

## FR-5 Freeze

- `verify.product.settlement_summary_contract_guard`
  - 校验结算汇总 contract 结构与金额口径
- `verify.product.project_flow.execution_settlement`
  - 校验 `execution -> settlement` 主链
- `verify.portal.settlement_slice_browser_smoke.host`
  - 校验真实浏览器链路：项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本 -> 付款 -> 结算
- `verify.release.settlement_slice_prepared`
  - Prepared 统一门禁入口
- `verify.release.settlement_slice_freeze`
  - Freeze 统一门禁入口

## 证据输出

- `artifacts/backend/product_settlement_summary_contract_guard.json`
- `artifacts/backend/product_project_flow_execution_settlement_smoke.json`
- `artifacts/codex/settlement-slice-browser-smoke/<timestamp>/summary.json`
