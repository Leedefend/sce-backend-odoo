# First Release Slice Decision

## FR-1 Decision

- status: `release-ready slice`
- slice: `project creation -> dashboard`
- decision date: `2026-03-23`

## Layer Target / Module / Reason

- Layer Target: `Release Governance Layer + Architecture Layer + Verify Layer`
- Module: `docs/ops/releases + docs/architecture + docs/product + docs/audit + Makefile`
- Reason: `将首发切片从冻结准备态推进为正式冻结态，并给出唯一发布口径与统一 gate`

## Decision Summary

- `项目创建 -> 驾驶舱` 已被认定为首发唯一可发布切片。
- 首发口径以 `docs/ops/releases/first_release_product_contract.md` 为唯一产品真源。
- 五层映射、dashboard block 白名单、前端边界锁定、验证矩阵均已冻结。
- 统一门禁固定为 `make verify.release.first_slice_freeze`。

## Included

- `项目创建`
- `自动初始化项目骨架`
- `跳转项目驾驶舱`
- `驾驶舱 entry + progress/risks/next_actions blocks`

## Excluded

- `计划`
- `执行`
- `成本闭环`
- `合同付款`
- `结算分析`

## Verification Baseline

- architecture baseline:
  - `make verify.product.final_slice_readiness_audit`
- project creation mainline:
  - `make verify.product.project_creation_mainline_guard`
- dashboard contract:
  - `make verify.product.project_dashboard_entry_contract_guard`
  - `make verify.product.project_dashboard_block_contract_guard`
- flow:
  - `make verify.product.project_flow.initiation_dashboard`
- browser:
  - `make verify.portal.first_release_slice_browser_smoke.host`
- unified gate:
  - `make verify.release.first_slice_freeze`

## Release Posture

- 当前结论：`可发布切片`
- 第二切片状态：`未启动`
- 第二切片只能以新批次进入，不得在 FR-1 冻结批次内继续扩写。

## Next Step

- 若继续推进，下一批次应单独声明第二切片范围：
  - `项目创建 -> 驾驶舱 -> 计划 -> 执行`
