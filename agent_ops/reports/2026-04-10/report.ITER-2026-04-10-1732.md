# ITER-2026-04-10-1732 Report

## Batch
- Batch: `P1-Batch55`
- Mode: `implement`
- Stage: `FORM-001 field truth-source audit`

## Architecture declaration
- Layer Target: `backend scene-orchestration contract supply governance`
- Module: `form contract field truth-source audit`
- Module Ownership: `smart_core`
- Kernel or Scenario: `scenario`
- Reason: 按缺口清单优先执行 FORM-001，先建立阻断级事实证据。

## Change summary
- 新增 `scripts/verify/form_field_truth_source_audit.py`
  - 拉取 `ui.contract(form)` 实网响应
  - 对比 `layout.fieldInfo` 与 `fields` 的 type/relation
  - 标记阻断项：关系字段被降级为 primitive（如 `many2one -> char`）
- 生成产物 `artifacts/contract/form_field_truth_source_v1.json`

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1732.yaml` ✅
- `python3 scripts/verify/form_field_truth_source_audit.py --json` ✅

## Audit conclusion
- 总问题数：`19`
- 阻断问题数：`10`
- 审计状态：`BLOCKED`
- 代表性阻断：
  - `partner_id`: canonical `many2one(res.partner)` vs layout `char`
  - `task_ids`: canonical `one2many(project.task)` vs layout `char`
  - `user_id`: canonical `many2one(res.users)` vs layout `char`

## Risk analysis
- 结论：`PASS_WITH_RISK`
- 风险级别：high
- 说明：关系字段真值源冲突会直接导致前端把关系字段渲染为文本输入，属于交付阻断问题。

## Rollback suggestion
- `git restore scripts/verify/form_field_truth_source_audit.py`

## Next suggestion
- 进入 FORM-001 修复批：后端统一字段真值源（`fields` 为唯一真值），`layout.fieldInfo` 仅保留布局补充。
