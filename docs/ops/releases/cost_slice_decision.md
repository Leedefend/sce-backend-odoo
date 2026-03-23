# Cost Slice Decision

## Decision

- status: `release-ready slice`
- slice: `project creation -> dashboard -> plan -> execution -> cost record -> cost summary`
- decision date: `2026-03-23`

## Layer Target / Module / Reason

- Layer Target: `Release Governance Layer + Architecture Layer + Verify Layer`
- Module: `docs/ops/releases + docs/architecture + Makefile + scripts/verify + frontend/apps/web`
- Reason: `将 FR-3 成本切片从 prepared 推进为正式 freeze，并固定唯一发布口径与统一 gate`

## Decision Summary

- `项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 成本汇总` 已被认定为 FR-3 唯一可发布切片。
- FR-3 口径以 `docs/ops/releases/cost_slice_product_contract.md` 为唯一产品真源。
- 五层映射、成本 contract、execution -> cost 接入、验证矩阵均已冻结。
- 统一门禁固定为 `make verify.release.cost_slice_freeze`。

## Included

- `execution -> cost` 入口
- `cost.tracking.enter`
- `cost.tracking.record.create`
- `cost_entry / cost_list / cost_summary`

## Excluded

- `成本预算`
- `成本分析`
- `成本审批`
- `合同付款`
- `结算分析`

## Verification Baseline

- architecture baseline:
  - `make verify.architecture.final_slice_readiness_audit`
- cost contract:
  - `make verify.product.cost_entry_contract_guard`
  - `make verify.product.cost_list_block_guard`
  - `make verify.product.cost_summary_block_guard`
- flow:
  - `make verify.product.project_flow.execution_cost`
- browser:
  - `make verify.portal.cost_slice_browser_smoke.host`
- unified gate:
  - `make verify.release.cost_slice_freeze`

## Release Posture

- 当前结论：`可发布切片`
- 合同/付款切片状态：`未启动`
- 合同/付款只能以新批次进入，不得在 FR-3 冻结批次内继续扩写。

## Next Step

- 若继续推进，下一批次应单独声明后续切片范围：
  - `合同/付款`
  - 或 `结算`
