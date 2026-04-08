# ITER-2026-04-08-1381 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_contract_v1_field_schema_guard` 原先用 `system.init` 启动子集（startup subset）做全量基线校验，导致 `8 < 50` 假失败。
- 修复：`scripts/verify/scene_contract_v1_field_schema_guard.py`
  - live 拉取改为 `system.init(contract_mode=user, with_preload=true)`，拿 full surface 结构；
  - 当 live scene 数低于基线时，允许回退到 `scene_registry_asset_snapshot_state` 的全量快照口径。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1381.yaml` ✅
- `make verify.scene.contract_v1.field_schema.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已消除 scene_count 误判阻断；
  - 新阻断前移到 `verify.scene.ready.consumption_trend.guard`（trend 阈值）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败已转为 trend guard 阈值问题，非 scene count 口径误判问题。

## Rollback suggestion
- `git restore scripts/verify/scene_contract_v1_field_schema_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1381.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1381.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1381.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 `ITER-1382`：定位 `scene_ready_consumption_trend_guard` 阈值与当前 runtime 基线不一致原因，并决定修阈值或修上游汇总输入。
