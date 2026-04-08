# ITER-2026-04-08-1387 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_base_contract_asset_coverage_guard` 使用默认 `system.init(user)` 口径读取 scene meta，导致 `base_contract_bound_scene_count` 在压缩口径下为 0，触发 `scene_bind_ratio=0` 误报。
- 修复：`scripts/verify/scene_base_contract_asset_coverage_guard.py`
  - live 拉取改为 `system.init(contract_mode=user, with_preload=true)`；
  - 当 scene meta 缺失/为 0 时，从 `scenes[].meta.compile_verdict` 回推 `scene_bound_count` 与 `compile_issue_scene_count`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1387.yaml` ✅
- `make verify.scene.base_contract_asset_coverage.guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 `scene_bind_ratio=0` 误报；
  - 新阻断前移到 `verify.role.capability_floor.prod_like`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为角色能力 floor 的新门禁，不属于本轮资产覆盖率口径问题。

## Rollback suggestion
- `git restore scripts/verify/scene_base_contract_asset_coverage_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1387.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1387.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1387.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：定位 `verify.role.capability_floor.prod_like` 的 capability floor 失败项并修复门禁口径/契约一致性。
