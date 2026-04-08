# ITER-2026-04-08-1392 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`scene_meta_trace_smoke` 将 `scene_channel` 作为 hud payload 与 meta.trace 的同名对比字段，而当前契约只在 meta.trace 提供 `scene_channel`，hud payload 提供 selector 字段。
- 修复：`scripts/verify/scene_meta_trace_smoke.py`
  - 新增 `REQUIRED_HUD_TRACE_KEYS`，仅对 hud payload 现有字段做一致性比对；
  - 保留 `scene_channel` 在 meta.trace 必填与 user/hud 模式一致性检查。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1392.yaml` ✅
- `make verify.scene.meta.trace.smoke DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮已清除 meta trace 阻断；
  - 新阻断前移到 `verify.contract.api.mode.smoke`（`http://localhost:8070` 超时）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败为运行环境可达性门禁（8070），不属于本轮 meta trace 字段口径问题。

## Rollback suggestion
- `git restore scripts/verify/scene_meta_trace_smoke.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1392.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1392.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1392.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：处理 `verify.contract.api.mode.smoke` 的 8070 可达性（启动对应服务或将 smoke 调整为可用端口/可降级策略）。
