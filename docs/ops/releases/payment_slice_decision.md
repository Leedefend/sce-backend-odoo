# Payment Slice Decision

## Decision

- status: `release-ready slice`
- slice: `project creation -> dashboard -> plan -> execution -> cost record -> payment record -> payment summary`
- decision date: `2026-03-23`

## Layer Target / Module / Reason

- Layer Target: `Release Governance Layer + Architecture Layer + Verify Layer`
- Module: `docs/ops/releases + docs/architecture + Makefile + scripts/verify + frontend/apps/web`
- Reason: `将 FR-4 付款切片从 prepared 推进为正式 freeze，并固定唯一发布口径与统一 gate`

## Decision Summary

- `项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本记录 -> 付款记录 -> 付款汇总` 已被认定为 FR-4 唯一可发布切片。
- FR-4 口径以 `docs/ops/releases/payment_slice_product_contract.md` 为唯一产品真源。
- 五层映射、payment contract、execution/cost -> payment 接入、验证矩阵均已冻结。
- 统一门禁固定为 `make verify.release.payment_slice_freeze`。

## Included

- `execution -> payment` 入口
- `cost -> payment` 入口
- `payment.enter`
- `payment.record.create`
- `payment_entry / payment_list / payment_summary`

## Excluded

- `合同条款`
- `审批流`
- `发票 / 税务`
- `复杂财务联动`
- `结算`

## Verification Baseline

- architecture baseline:
  - `make verify.architecture.final_slice_readiness_audit`
- payment contract:
  - `make verify.product.payment_entry_contract_guard`
  - `make verify.product.payment_list_block_guard`
  - `make verify.product.payment_summary_block_guard`
- flow:
  - `make verify.product.project_flow.execution_payment`
- browser:
  - `make verify.portal.payment_slice_browser_smoke.host`
- unified gate:
  - `make verify.release.payment_slice_freeze`

## Release Posture

- 当前结论：`可发布切片`
- 结算切片状态：`未启动`
- 结算只能以新批次进入，不得在 FR-4 冻结批次内继续扩写。

## Next Step

- 若继续推进，下一批次应单独声明后续切片范围：
  - `结算`
  - 或其他独立经营闭环切片
