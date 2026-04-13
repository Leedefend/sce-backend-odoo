# ITER-2026-04-10-1806 Report

## Batch
- Batch: `FORM-Backend-R2`
- Mode: `implement`
- Stage: `project form user governance de-prune tabs`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `project form governance policy`
- Module Ownership: `addons/smart_core`
- Kernel or Scenario: `kernel`
- Reason: 解析链可产出完整 notebook/page，但 user 治理策略会把 project form 结构过度裁剪。

## Change summary
- 修改 `addons/smart_core/utils/contract_governance.py` 的 `_govern_project_form_contract_for_user`：
  - 停止将 `data.fields` 裁剪为 `selected` 子集，保留完整字段映射。
  - 停止调用 `_filter_project_form_layout(data, selected)`，保留 parser-native notebook/page 树。
  - `permissions.field_groups` 保持原样，不再按 `selected_set` 二次裁剪。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1806.yaml` → `PASS`
- `rg -n "_govern_project_form_contract_for_user|_filter_project_form_layout|Keep parser-native notebook/page tree" addons/smart_core/utils/contract_governance.py` → `PASS`
- `make restart` → `PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：`medium`
- 风险说明：user surface 会显示更多 project form 结构，但这是本轮目标（原生结构对齐）。

## Rollback suggestion
- `git restore addons/smart_core/utils/contract_governance.py`

## Next suggestion
- 刷新 `structure_audit=1` 页面，确认 `contract 输入（views.form.layout）` 与业务 tab 数量恢复一致。
