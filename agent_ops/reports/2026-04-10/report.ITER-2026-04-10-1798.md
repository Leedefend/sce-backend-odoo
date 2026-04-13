# ITER-2026-04-10-1798 Report

## Batch
- Batch: `FORM-Contract-RootFix-R1`
- Mode: `implement`
- Stage: `action-bound form view selection root fix`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `app.view.config action-specific view loader`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: 同一动作存在多个 form 视图候选时，错误命中精简视图会导致业务页签未进入 contract。

## Change summary
- 文件：`addons/smart_core/app_config_engine/models/app_view_config.py`
- `_safe_get_view_data` 新增动作绑定候选视图聚合：
  - 收集 `form_view_ref/tree_view_ref`、`act.views`、`act.view_id`、`ir.actions.act_window.view`。
- 新增 form 视图择优策略：
  - 对候选 `view_id` 逐个加载，按 `notebook/page` 数量（+arch 长度）打分。
  - 选取结构最完整的候选作为 contract 视图来源。
- 保持 tree/其他视图原有选择逻辑（单候选优先）。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1798.yaml` → `PASS`
- `rg -n "candidate_view_ids|count_notebook_pages|load_action_specific_view" addons/smart_core/app_config_engine/models/app_view_config.py` → `PASS`
- `make restart` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：动作有多个 form 视图时选择策略变更，可能影响个别菜单的优先视图，但仅在 action 绑定候选内择优，不跨模型。

## Rollback suggestion
- 文件级回滚：
  - `git restore addons/smart_core/app_config_engine/models/app_view_config.py`
- 服务恢复：
  - `make restart && make frontend.restart`

## Next suggestion
- 让前端刷新同一记录并回传 `structure_audit=1` 摘要，确认业务 tab 是否进入 `views.form.layout`。
