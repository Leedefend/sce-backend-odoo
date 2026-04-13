# ITER-2026-04-10-1764 Report

## Batch
- Batch: `FORM-Batch1/2 bridge`
- Mode: `implement`
- Stage: `ui.contract v2 runtime truth-source alignment`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `ui.contract v2 runtime form truth-source closure`
- Module Ownership: `smart_core v2 service`
- Kernel or Scenario: `kernel`
- Reason: 运行态 `ui.contract` 仍返回旧结构；需在真实 v2 服务链根因修复，而非编排兜底。

## Change summary
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - `_sync_form_layout_field_info` 改为轻量投影：`fieldInfo` 仅保留 `name/label/widget/colspan/modifiers`。
  - 移除 `semantic_page.form_semantics.layout` 重复树，改为 `layout_source=views.form.layout` + `layout_section_count`。
  - 新增 `_fill_statusbar_states_from_selection`：当 `statusbar.field` 指向 selection 字段时生成 `states`，并写入 `states_source`。
  - fallback contract 同步为单真值源语义（不再复制 layout）。
  - runtime pipeline 接入 statusbar states 填充步骤。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1764.yaml` ✅
- `make restart` ✅
- `make frontend.restart` ✅
- 重新抓取运行态快照到 `tmp/json/form.json` ✅
- `python3 scripts/verify/form_layout_single_source_audit.py --json --input tmp/json/form.json` ✅
  - `status=PASS`
  - `has_semantic_layout_tree=false`
  - `layout_source=views.form.layout`
- `python3 scripts/verify/form_field_truth_source_audit.py --json --input tmp/json/form.json` ✅
  - focus 字段通过；`fieldInfo` 不再包含禁用真值字段
- `python3 scripts/verify/form_statusbar_states_audit.py --json --input tmp/json/form.json` ✅
  - `statusbar.field=lifecycle_state`
  - `states_count=7`
  - `states_source=fields.selection`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：`form_field_truth_source_audit` 对部分未布局字段仍提示非阻断问题（不影响本轮根因修复）；后续可在审计脚本口径细化。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/ui_contract_service.py`

## Next suggestion
- 进入下一轮 `FORM-Batch2 / 102-2`：`button_box` 与 `stat_buttons` 语义分离，继续贴近原生 surface。
