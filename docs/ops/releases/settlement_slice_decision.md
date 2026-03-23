# Settlement Slice Decision

## Decision

- status: `release-ready slice`
- slice: `project creation -> dashboard -> plan -> execution -> cost -> payment -> settlement result`
- decision date: `2026-03-23`

## Layer Target / Module / Reason

- Layer Target: `Release Governance Layer + Architecture Layer + Verify Layer`
- Module: `docs/ops/releases + docs/architecture + Makefile + scripts/verify + frontend/apps/web`
- Reason: `将 FR-5 结算切片从 prepared 推进为正式 freeze，并固定唯一发布口径与统一 gate`

## Decision Summary

- `项目创建 -> 驾驶舱 -> 计划 -> 执行 -> 成本 -> 付款 -> 结算结果` 已被认定为 FR-5 唯一可发布切片。
- FR-5 口径以 `docs/ops/releases/settlement_slice_product_contract.md` 为唯一产品真源。
- 五层映射、settlement summary contract、execution/cost/payment -> settlement 接入、验证矩阵均已冻结。
- 统一门禁固定为 `make verify.release.settlement_slice_freeze`。

## Included

- `execution -> settlement` 入口
- `cost -> settlement` 入口
- `payment -> settlement` 入口
- `settlement.enter`
- `settlement.block.fetch`
- `settlement_summary`

## Excluded

- `合同结算规则`
- `审批`
- `发票 / 税务`
- `多维分析`
- `报表体系`
- `写入型结算动作`

## Verification Baseline

- architecture baseline:
  - `make verify.architecture.final_slice_readiness_audit`
- settlement contract:
  - `make verify.product.settlement_summary_contract_guard`
- flow:
  - `make verify.product.project_flow.execution_settlement`
- browser:
  - `make verify.portal.settlement_slice_browser_smoke.host`
- unified gate:
  - `make verify.release.settlement_slice_freeze`

## Release Posture

- 当前结论：`可发布切片`
- 结算切片状态：`正式冻结`
- 后续若继续推进，只能以新批次扩展经营分析或其他独立切片，不得在 FR-5 冻结批次内继续扩写。

## Next Step

- 若继续推进，下一批次应单独声明后续切片范围：
  - `经营分析`
  - 或其他独立经营闭环切片
