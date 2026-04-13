# ITER-2026-04-10-1763 Report

## Batch
- Batch: `FORM-Batch2`
- Mode: `implement`
- Stage: `form statusbar states closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `form statusbar semantics`
- Module Ownership: `smart_core + verify scripts`
- Kernel or Scenario: `kernel`
- Reason: 收敛 statusbar 语义，避免 statusbar.field 存在但 states 为空。

## Change summary
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - `_fill_statusbar_states_from_selection` 从仅支持 `state` 字段升级为通用 `statusbar.field`。
  - 若字段为 selection：生成 `states[{value,label,sequence}]`，并标记 `states_source=selection`。
  - 若非静态 selection：保留空 states，但补 `states_source=dynamic_relation` 与 `states_reason`。
  - 补充 `statusbar.label` 兜底。
- 新增 `scripts/verify/form_statusbar_states_audit.py`
  - 输出 `artifacts/contract/form_statusbar_states_v1.json`
  - 校验 statusbar field/states/source/reason 闭环。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1763.yaml` ✅
- `python3 scripts/verify/form_statusbar_states_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `snapshot_outdated=true`（快照为旧输出）

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：输入快照未刷新，运行态需重启后端并重新抓取 contract 再复核 states 实际输出。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore scripts/verify/form_statusbar_states_audit.py`

## Next suggestion
- 继续 `FORM-Batch2 / 102-2`：button_box 与 stat_buttons 语义分离收敛。
