# ITER-2026-04-08-1389 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`native_surface_integrity_guard` 仍强制要求 `ui.contract(native)` 成功返回，而当前策略已明确禁用 native 交付并提示使用 scene-ready contract。
- 修复：`scripts/verify/native_surface_integrity_guard.py`
  - 保留 native 成功路径校验；
  - 新增“策略禁用可接受”路径：当返回 `INTERNAL_ERROR` 且错误信息匹配 `native ui.contract op is disabled ... use scene-ready contract` 时判定为 PASS（policy-aligned evidence）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1389.yaml` ✅
- `make verify.native_surface_integrity_guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 native surface integrity 阻断；
  - 新阻断前移到 `verify.contract.surface_mapping_guard`（同样仍要求 `ui.contract.native` 成功）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为 surface mapping guard 与最新 native 禁用策略不一致，不属于本轮 native surface integrity guard。

## Rollback suggestion
- `git restore scripts/verify/native_surface_integrity_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1389.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1389.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1389.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：将 `surface_mapping_guard` 的 native 分支校验与“native 禁用、scene-ready 接管”策略对齐。
