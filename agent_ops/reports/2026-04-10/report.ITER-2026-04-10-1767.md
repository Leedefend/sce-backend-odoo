# ITER-2026-04-10-1767 Report

## Batch
- Batch: `FORM-Batch3`
- Mode: `implement`
- Stage: `form x2many subview depth closure`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `form subview depth and relation semantics`
- Module Ownership: `smart_core v2 service + verify script`
- Kernel or Scenario: `kernel`
- Reason: 修复 subviews 仅有 columns/policies 而 fields 为空的问题，补齐复杂表单子视图消费语义。

## Change summary
- 更新 `addons/smart_core/v2/services/ui_contract_service.py`
  - 新增 `_infer_relation_fields_meta`：按 relation 模型与 columns 生成字段元数据（type/label/relation/required/readonly/selection）。
  - 增强 `_ensure_form_x2many_subviews`：
    - 为 `tree.columns` 补齐 `fields` 元数据映射
    - 补齐 `relation_model`
    - 补齐 `entry.default/can_open`
    - 补齐 `policies.can_open`
- 新增 `scripts/verify/form_subview_depth_audit.py`
  - 校验 x2many subview 的 columns 与 fields 对齐
  - 校验 relation_model 与 policies 基础语义
  - 输出 `artifacts/contract/form_subview_depth_v1.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1767.yaml` ✅
- `python3 -m py_compile addons/smart_core/v2/services/ui_contract_service.py scripts/verify/form_subview_depth_audit.py` ✅
- `make restart` ✅
- 重新抓取运行态快照：`tmp/json/form.json` ✅
- `python3 scripts/verify/form_subview_depth_audit.py --json --input tmp/json/form.json` ✅
  - `summary.status=PASS`
  - `x2many_subview_count=2`
  - `task_ids fields=4/columns=4`
  - `collaborator_ids fields=1/columns=1`

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：字段元数据来自 relation `fields_get`，为运行时推导；若 relation 字段配置变化会自动反映，不引入硬编码结构风险。

## Rollback suggestion
- `git restore addons/smart_core/v2/services/ui_contract_service.py`
- `git restore scripts/verify/form_subview_depth_audit.py`

## Next suggestion
- 进入 `FORM-Batch3 / 103-3`：动作真值源去重（buttons/header/button_box/action_groups 主从统一）。
