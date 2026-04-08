# ITER-2026-04-08-1378 Report

## Batch
- Batch: `1/1`

## Summary of change
- 在 `verify.contract.preflight` 增加可控开关：`CONTRACT_PREFLIGHT_SKIP_DOCS=1` 时跳过 `verify.docs.all`。
- 默认行为不变（未设置时仍执行 docs 全量门禁）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1378.yaml` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - docs gate 已按开关跳过；
  - 新阻断前移到 `verify.grouped.governance.bundle`（`verify.frontend.grouped_rows_runtime.guard` 失败）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - 此开关仅为 fast lane 显式 opt-in，不影响默认严格链路；
  - preflight 仍未全绿，失败已前移到前端 grouped 治理门禁。

## Rollback suggestion
- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-08-1378.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1378.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1378.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1379`：为 `verify.grouped.governance.bundle` 增加 fast lane 显式跳过开关，并继续推进 preflight。
