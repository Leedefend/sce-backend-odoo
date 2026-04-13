# ITER-2026-04-10-1770 Report

## Batch
- Batch: `FORM-Batch4`
- Mode: `implement`
- Stage: `form render-profile consumption spec freeze`

## Architecture declaration
- Layer Target: `Backend contract semantic layer`
- Module: `form render-profile consumption specification`
- Module Ownership: `smart_core + frontend consumer`
- Kernel or Scenario: `kernel`
- Reason: render-surfaces 已落地，需冻结消费口径，防止后续消费漂移。

## Change summary
- 新增文档 `docs/architecture/form_contract_render_profile_v1.md`
  - 固定单真值源规则（`views.form.layout` + `layout_source`）
  - 固定 `fields` 与 `layout.fieldInfo` 角色边界
  - 固定 `render_surfaces.create/edit/readonly` 消费规则
  - 定义 `modifiers priority`
  - 定义 `actions priority`
  - 固定 subview profile/structure 消费关系
  - 明确兼容策略（additive + documented-first）

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1770.yaml` ✅
- `rg -n "render_surfaces|layout_source|fields as truth source|modifiers priority|actions priority" docs/architecture/form_contract_render_profile_v1.md` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：本轮为规范冻结，不改运行时代码；风险主要在后续执行一致性，已通过规则项固化。

## Rollback suggestion
- `git restore docs/architecture/form_contract_render_profile_v1.md`

## Next suggestion
- 进入前端消费链切换批：按本规范逐步把 form 页面消费主路径切到 `render_surfaces.<profile>`。
