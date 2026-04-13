# ITER-2026-04-10-1761 Report

## Batch
- Batch: `FORM-Batch1`
- Mode: `implement`
- Stage: `form field truth-source closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `ui.contract form field truth source governance`
- Module Ownership: `smart_core + verify scripts`
- Kernel or Scenario: `kernel`
- Reason: 统一字段真值源，避免 layout.fieldInfo 与 fields 双真值冲突。

## Change summary
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - `_sync_form_layout_field_info` 改为输出轻量 `fieldInfo`：
    - 保留：`name/label/widget/colspan/modifiers`
    - 去除：`type/relation/required/readonly/invisible/help` 等字段真值
  - 字段类型与关系语义统一由 `fields` 提供。
- 更新 `scripts/verify/form_field_truth_source_audit.py`
  - 改为基于输入快照文件审计（默认 `tmp/json/form.json`）。
  - 增加 code-guard：校验后端代码已切换为轻量 `fieldInfo` 投影。
  - 生成 `artifacts/contract/form_field_truth_source_v1.json`。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1761.yaml` ✅
- `python3 scripts/verify/form_field_truth_source_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `snapshot_outdated=true`（当前 `tmp/json/form.json` 为改动前快照）

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：运行态快照未刷新；代码侧真值源收敛门禁已通过，需重启后端后重新抓取 `form.json` 复核。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore scripts/verify/form_field_truth_source_audit.py`

## Next suggestion
- 继续 `FORM-Batch1 / Task 101-3`：widget 精度收敛（html/boolean/selection/relation widget 匹配）。
