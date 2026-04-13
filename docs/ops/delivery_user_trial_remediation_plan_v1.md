# Delivery User Trial Remediation Plan v1

## Input Baseline

- issue_board: `artifacts/delivery/user_trial_issue_board_v1.json`
- execution_log: `docs/ops/delivery_user_trial_execution_log_v1.md`
- freeze_baseline: `docs/ops/delivery_freeze_baseline_v1.md`

## Planning Principle

- 仅处理 `P2/P3` 且 `status=OPEN` 的问题。
- 不扩展功能边界，仅做可交付体验优化。
- 每个问题映射到单独修复批次，保持可验证与可回滚。

## Remediation Backlog

| issue_id | severity | menu_id | title | target_batch | owner | verify_artifact |
| --- | --- | --- | --- | --- | --- | --- |
| UT-20260410-002 | P3 | 315 | 列表页提示文案可进一步简化 | ITER-2026-04-10-1709 | frontend-runtime | `artifacts/delivery/remediation_1709_summary.json` |
| UT-20260410-003 | P3 | 317 | 空态文案建议增加业务示例 | ITER-2026-04-10-1710 | frontend-runtime | `artifacts/delivery/remediation_1710_summary.json` |

## Batch Plan

### ITER-2026-04-10-1709

- scope: `menu_id=315` 列表页提示文案优化
- acceptance:
  - 文案符合“简短、可执行、无技术术语”
  - 页面可打开/可操作/可返回不回退
  - menu smoke 维持 `fail_count=0`

### ITER-2026-04-10-1710

- scope: `menu_id=317` 空态文案增强（业务示例）
- acceptance:
  - 空态可读并提供下一步建议
  - 错误/空态可观测字段保持一致
  - menu smoke 维持 `fail_count=0`

## Exit Criteria

- `UT-20260410-002` 状态更新为 `VERIFIED` 或 `CLOSED`
- `UT-20260410-003` 状态更新为 `VERIFIED` 或 `CLOSED`
- 无新增 `P0/P1` 问题
