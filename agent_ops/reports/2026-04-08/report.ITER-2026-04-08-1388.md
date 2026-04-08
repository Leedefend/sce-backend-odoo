# ITER-2026-04-08-1388 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`role_capability_floor_prod_like` 仅读取 legacy `data.capabilities`，而当前 `system.init` 已演进为 `role_surface.scene_candidates` / `scene_ready_contract_v1.scenes` 主口径，导致全角色能力数误判为 0。
- 修复：`scripts/verify/role_capability_floor_prod_like.py`
  - `system.init` 调用改为 `with_preload=true`；
  - capability 计数增加兼容回退链：`capabilities -> role_surface.scene_candidates -> scene_ready_contract_v1.scenes`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1388.yaml` ✅
- `make verify.role.capability_floor.prod_like DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 capability floor 全角色 0 误报；
  - 新阻断前移到 `verify.native_surface_integrity_guard`（`ui.contract.native_surface` 已被禁用）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为 native surface integrity 守卫与最新 `ui.contract` 策略不一致，不属于本轮 capability floor 问题。

## Rollback suggestion
- `git restore scripts/verify/role_capability_floor_prod_like.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1388.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1388.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1388.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：将 `native_surface_integrity_guard` 与“native ui.contract 禁用、应走 scene-ready contract”策略对齐。
