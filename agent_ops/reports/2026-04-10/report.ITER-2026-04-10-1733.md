# ITER-2026-04-10-1733 Report

## Batch
- Batch: `P1-Batch56`
- Mode: `implement`
- Stage: `FORM-001 remediation`

## Architecture declaration
- Layer Target: `backend scene-orchestration contract supply`
- Module: `view parser + v2 ui.contract runtime normalization`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: 修复 layout.fieldInfo 与 fields 真值源不一致，解除关系字段降级阻断。

## Change summary
- 更新 `addons/smart_core/app_config_engine/services/view_Parser/base.py`
  - 新增字段类型/关系解析 helper（兼容 `type/ttype`、`relation/comodel_name`）。
- 更新 `addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py`
  - 表单/列表字段类型解析改为 canonical 优先，`fieldInfo` relation 按 canonical 回填。
- 更新 `addons/smart_core/app_config_engine/services/contract_service.py`
  - 增加 form layout `fieldInfo` 真值源同步（fields 为 canonical）。
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 在 v2 `ui.contract` runtime 路径增加 layout `fieldInfo` 同步，确保 v2 主链生效。

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1733.yaml` ✅
- `make restart` ✅
- `python3 scripts/verify/form_field_truth_source_audit.py --json` ✅

## Audit delta
- 修复前（1732）：`issue_count=19`, `blocking_count=10`, `status=BLOCKED`
- 修复后（1733）：`issue_count=0`, `blocking_count=0`, `status=PASS`

## Risk analysis
- 结论：`PASS`
- 风险级别：medium-low
- 说明：变更限定于契约语义供给归一，不触达业务事实、ACL 或财务语义。

## Rollback suggestion
- `git restore addons/smart_core/app_config_engine/services/view_Parser/base.py`
- `git restore addons/smart_core/app_config_engine/services/view_Parser/parsers Tree Form.py`
- `git restore addons/smart_core/app_config_engine/services/contract_service.py`
- `git restore addons/smart_core/v2/services/ui_contract_service.py`

## Next suggestion
- 进入 FORM-003（动态 modifiers）或 FORM-006（动作真值源收敛）批次。
