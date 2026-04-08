# ITER-2026-04-08-1385 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_engine_migration_matrix_guard` 固定读取单一 `scene_registry_asset_snapshot_state.json`（当前为 startup subset 8 场景），导致 full-scene 迁移矩阵出现缺失 state 与 non-asset 误报。
- 修复：`scripts/verify/scene_engine_migration_matrix_guard.py`
  - 新增状态候选扫描（`scene_registry_asset_snapshot_state*.json`）；
  - 按 `scene_count`（并列时按 `per_scene` 数）自动选择最优 full-scene 状态；
  - 报告中增加 `selected_state_file` 追踪实际口径来源。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1385.yaml` ✅
- `make verify.scene.engine_migration.matrix.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 migration matrix 口径误报；
  - 新阻断前移到 `verify.scene.base_contract_source_mix.guard`：`scene_count below threshold: 8 < 50`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为 source mix guard 的口径问题，不属于本轮 migration matrix guard。

## Rollback suggestion
- `git restore scripts/verify/scene_engine_migration_matrix_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1385.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1385.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1385.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：按同一全场景口径策略修复 `scene_base_contract_source_mix_guard` 的 `8 < 50` 阻断。
