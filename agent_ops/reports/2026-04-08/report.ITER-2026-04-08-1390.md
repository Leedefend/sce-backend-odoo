# ITER-2026-04-08-1390 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`surface_mapping_guard` 对 `native` 分支仍执行 `require_ok` 强校验，而当前策略中 native ui.contract 已禁用并返回政策提示。
- 修复：`scripts/verify/surface_mapping_guard.py`
  - `native` 分支新增策略兼容路径：当返回 `INTERNAL_ERROR` 且消息包含 `native ui.contract op is disabled` 与 `scene-ready contract` 时，判为 PASS（`native_disabled_expected`）；
  - `user/hud` 分支保持严格 `require_ok + mapping` 校验不变。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1390.yaml` ✅
- `make verify.contract.surface_mapping_guard DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 surface mapping 阻断；
  - 新阻断前移到 `verify.scene.hud.trace.smoke`：`system.init hud missing trace field: scene_channel`。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为 hud trace smoke 与当前 hud trace 字段语义不一致，不属于本轮 surface mapping 问题。

## Rollback suggestion
- `git restore scripts/verify/surface_mapping_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1390.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1390.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1390.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：对齐 `scene_hud_trace_smoke` 与当前 `system.init(hud)` trace 字段规范（兼容 `scene_channel_selector`/`channel_selector`）。
