# ITER-2026-04-08-1386 Report

## Batch
- Batch: `1/1`

## Summary of change
- 按同一根因一次性修复三处 snapshot-state 消费 guard 的口径问题：
  - `scripts/verify/scene_base_contract_source_mix_guard.py`
  - `scripts/verify/scene_no_action_scene_guard.py`
  - `scripts/verify/scene_sample_registry_diff_guard.py`
- 修复方式统一为：从 `scene_registry_asset_snapshot_state*.json` 中选择 full-scene 最优状态（按 `scene_count`，平局按 `per_scene` 数）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1386.yaml` ✅
- `make verify.scene.base_contract_source_mix.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `make verify.scene.no_action_scene.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `make verify.scene.sample_registry_diff.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮同类口径阻断已清除；
  - 新阻断前移到 `verify.scene.base_contract_asset_coverage.guard`：`scene_bind_ratio below threshold: 0.0000 < 0.1500`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为新的资产覆盖率门禁，不属于本轮 snapshot-state 单文件口径问题。

## Rollback suggestion
- `git restore scripts/verify/scene_base_contract_source_mix_guard.py`
- `git restore scripts/verify/scene_no_action_scene_guard.py`
- `git restore scripts/verify/scene_sample_registry_diff_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1386.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1386.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1386.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：定位 `scene_base_contract_asset_coverage_guard` 的 `scene_bind_ratio=0.0` 是否同样由运行态状态口径/字段映射导致，并按同样原则修正。
