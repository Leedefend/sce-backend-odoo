# ITER-2026-04-08-1391 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_hud_trace_smoke` 仍将 `scene_channel` 视作 hud 顶层必填并要求与 `channel_selector` 强等值；当前契约中 `scene_channel` 在 `meta.scene_trace`，hud 顶层为 `channel_selector/channel_source_ref`。
- 修复：`scripts/verify/scene_hud_trace_smoke.py`
  - 拆分 hud 必填字段与 meta trace 必填字段；
  - 保留 hud 与 meta 对同名字段的一致性校验；
  - 移除 `scene_channel == channel_selector` 的错误强等值断言。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1391.yaml` ✅
- `make verify.scene.hud.trace.smoke DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 hud trace 阻断；
  - 新阻断前移到 `verify.scene.meta.trace.smoke`（同类 `scene_channel` 强等值校验）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败是同类 meta trace smoke 口径不一致，不属于本轮 hud trace smoke。

## Rollback suggestion
- `git restore scripts/verify/scene_hud_trace_smoke.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1391.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1391.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1391.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：按同样策略对齐 `scene_meta_trace_smoke` 的 `scene_channel` 字段断言语义。
