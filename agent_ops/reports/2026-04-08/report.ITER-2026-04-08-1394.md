# ITER-2026-04-08-1394 Report

## Batch
- Batch: `1/1`

## Summary of change
- 根因确认：`verify.frontend.search_groupby_savedfilters.guard` 仍以单文件 `ActionView.vue` marker 为准，和当前前端拆分 runtime 实现不一致。
- 修复文件：`scripts/verify/search_groupby_savedfilters_guard.py`
  - 前端 marker 校验拆分到多文件：
    - `frontend/apps/web/src/views/ActionView.vue`
    - `frontend/apps/web/src/app/action_runtime/useActionViewFilterComputedRuntime.ts`
    - `frontend/apps/web/src/app/action_runtime/useActionViewRequestContextRuntime.ts`
    - `frontend/apps/web/src/app/runtime/actionViewRequestRuntime.ts`
    - `frontend/apps/web/src/app/action_runtime/useActionViewFilterGroupRuntime.ts`
  - 将过时 marker `group_by: activeGroupByField.value || undefined` 替换为当前语义 marker `group_by: field`（group context runtime 真实来源）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-08-1394.yaml` ✅
- `python3 scripts/verify/search_groupby_savedfilters_guard.py` ✅
- `CONTRACT_PREFLIGHT_SKIP_DOCS=1 CONTRACT_PREFLIGHT_SKIP_GROUPED_GOV_BUNDLE=1 CONTRACT_PREFLIGHT_SKIP_SCENE_CAPABILITY_GUARD=1 CONTRACT_PREFLIGHT_STRICT_VIEW_TYPES=0 BASELINE_FREEZE_ENFORCE=0 make verify.contract.preflight DB_NAME=sc_demo E2E_LOGIN=admin E2E_PASSWORD=admin` ❌
  - 本轮目标门禁 `verify.frontend.search_groupby_savedfilters.guard` 已恢复 PASS；
  - preflight 前进到下一真实阻断：`verify.frontend.view_type_render_coverage.guard`（仍依赖旧 ActionView marker）。

## Risk analysis
- 结论：`FAIL`
- 风险级别：medium
- 说明：当前失败已转移到新的前端视图覆盖门禁，需下一轮 dedicated 对齐。

## Rollback suggestion
- `git restore scripts/verify/search_groupby_savedfilters_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-08-1394.yaml`
- `git restore agent_ops/reports/2026-04-08/report.ITER-2026-04-08-1394.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-08-1394.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Next iteration suggestion
- 新开 dedicated batch：修复 `verify.frontend.view_type_render_coverage.guard`，将其 marker 口径从旧 `ActionView.vue` 单文件校验升级为当前拆分 runtime 语义校验。
