# ITER-2026-04-10-1799 Report

## Batch
- Batch: `FORM-Contract-RootFix-R2`
- Mode: `implement`
- Stage: `form fallback richest-view selection fix`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `app.view.config safe_get_view_data fallback strategy`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: action 未显式绑定 form 视图时默认命中精简 form，导致业务 tab 未进入 contract。

## Change summary
- 文件：`addons/smart_core/app_config_engine/models/app_view_config.py`
- 在 `candidate_view_ids` 为空且 `view_type=form` + `contract_action_id` 场景新增 fallback 策略：
  - 从 `ir.ui.view` 中收集该模型全部 active form 视图候选。
  - 使用既有 `count_notebook_pages` + arch 长度打分择优。
  - 选取结构最丰富的 form 视图作为 contract 来源。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1799.yaml` → `PASS`
- `rg -n "fallback_candidates|fallback 候选|count_notebook_pages" addons/smart_core/app_config_engine/models/app_view_config.py` → `PASS`
- `make restart` → `PASS`
- `make frontend.restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium-low`
- 风险说明：form fallback 选择策略变更，影响 action 未显式绑定 form 的场景；逻辑仍限定在同模型、同视图类型候选内择优。

## Rollback suggestion
- 文件级回滚：
  - `git restore addons/smart_core/app_config_engine/models/app_view_config.py`
- 服务恢复：
  - `make restart && make frontend.restart`

## Next suggestion
- 刷新 `structure_audit=1` 页面并回传摘要，确认 `views.form.layout page` 是否从 3 提升到业务 tab 规模。
