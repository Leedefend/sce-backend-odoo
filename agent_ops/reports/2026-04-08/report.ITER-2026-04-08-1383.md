# ITER-2026-04-08-1383 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_registry_asset_snapshot_guard` 使用 `system.init(contract_mode=user)` 的默认压缩口径，`scene_ready_contract_v1.meta` 中 `base_contract_bound_scene_count` 缺失，导致误判为 `0`。
- 修复：`scripts/verify/scene_registry_asset_snapshot_guard.py`
  - live 拉取改为 `system.init(contract_mode=user, with_preload=true)`；
  - 对 `base_contract_bound_scene_count` 增加回退推导：当 meta 缺失或为 `0` 时，以 `per_scene.base_contract_bound=true` 的计数作为兜底。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1383.yaml` ✅
- `make verify.scene.registry_asset_snapshot.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 registry snapshot guard 的 `0 < 1` 误报；
  - 新阻断前移回 `verify.scene.contract_v1.field_schema.guard`：`scene count below baseline: 8 < 50`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为场景基线数量与运行态输出口径不一致，不属于本轮 registry snapshot guard 计数误报问题。

## Rollback suggestion
- `git restore scripts/verify/scene_registry_asset_snapshot_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1383.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1383.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1383.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：聚焦 `scene_contract_v1_field_schema_guard` 的 `8 < 50` 基线口径，决定是恢复 full-scene 输出口径，还是将 guard 固定到与当前运行态一致的可验证口径。
