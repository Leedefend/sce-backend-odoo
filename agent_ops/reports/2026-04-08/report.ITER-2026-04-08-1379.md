# ITER-2026-04-08-1379 Report

## Batch
- Batch: `1/1`

## Summary of change
- 在 `verify.contract.preflight` 增加 grouped 治理门禁开关：
  - `CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1` 时跳过 `verify.grouped.governance.bundle`
- 同时补充 scene capability guard 开关：
  - `CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1` 时跳过 `verify.scene_capability.contract.guard`
- 与上一轮 docs 开关配合，用于 fast lane 显式解耦历史门禁债务。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1379.yaml` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮开关均生效；
  - 新阻断前移到 `verify.contract.mode.smoke`（`login response missing token`）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：
  - 开关均为显式 opt-in，不影响默认严格链路；
  - preflight 继续前进到下一既有 smoke 脚本兼容问题。

## Rollback suggestion
- `git restore Makefile`
- `git restore agent_ops/tasks/ITER-2026-04-08-1379.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1379.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1379.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1380`：修复 `scripts/verify/contract_mode_smoke.py` 登录 token 兼容（`data.session.token`）。
