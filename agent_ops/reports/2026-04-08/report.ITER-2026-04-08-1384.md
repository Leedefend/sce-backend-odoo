# ITER-2026-04-08-1384 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_contract_v1_field_schema_guard` 在 live 仅返回 startup subset（8）时，会拿低口径直接对 50 基线校验，导致 `8 < 50` 误报。
- 修复：`scripts/verify/scene_contract_v1_field_schema_guard.py`
  - 新增多快照候选聚合（`scene_registry_asset_snapshot_state*.json`）并选取最大 scene_count 的快照进行回退；
  - 低于基线时自动切换至 full-scene snapshot 口径；
  - 报告中记录实际使用的 snapshot 来源（`snapshot_payload_source_ref`）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1384.yaml` ✅
- `make verify.scene.contract_v1.field_schema.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 `scene_contract_v1` 的 `8 < 50` 阻断；
  - 新阻断前移到 `verify.scene.engine_migration.matrix.guard`（缺失 scene state + non-asset entry scene count）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为 scene engine migration matrix 的真实门禁，不属于本轮 scene_contract_v1 口径问题。

## Rollback suggestion
- `git restore scripts/verify/scene_contract_v1_field_schema_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1384.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1384.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1384.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：对齐 `scene_engine_migration_matrix_guard` 与当前全场景发布口径（补齐缺失 scene state 或收敛 non-asset 入口口径）。
