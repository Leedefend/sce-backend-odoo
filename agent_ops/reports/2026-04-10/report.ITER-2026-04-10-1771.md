# ITER-2026-04-10-1771 Report

## Batch
- Batch: `FORM-Frontend-Switch`
- Mode: `implement`
- Stage: `frontend render-surfaces consumer switch`

## Architecture declaration
- Layer Target: `Frontend contract-consumer runtime`
- Module: `ContractFormPage profile-surface consumer`
- Module Ownership: `frontend/apps/web`
- Kernel or Scenario: `scenario`
- Reason: 将表单消费主路径切到 `render_surfaces.<profile>`，与后端新契约保持一致。

## Change summary
- 更新 `frontend/apps/web/src/pages/ContractFormPage.vue`
  - 新增 `resolveSurfaceActionRows`：优先读取 `render_surfaces.<profile>.actions.*`，缺失回退到 `views.form.*`。
  - 新增 `activeRenderSurface`：按 `renderProfile` 解析当前 profile surface。
  - 新增 `one2manyPolicies`：合并 `render_surfaces.<profile>.subviews.policies` 与 `views.form.subviews.policies`。
  - x2many 行为对齐 profile policy：
    - `addOne2manyRow` 受 `canCreate` 控制
    - `setOne2manyRowField` 受 `inlineEdit` 控制
    - `removeOne2manyRow` 受 `canUnlink` 控制

## Verification result
- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-10-1771.yaml` ✅
- `rg -n "render_surfaces|activeRenderSurface|one2manyPolicies" frontend/apps/web/src/pages/ContractFormPage.vue` ✅
- `make frontend.restart` ✅

## Risk analysis
- 结论：`PASS`
- 风险级别：low
- 风险说明：本轮保留 `views.form.*` 回退路径，避免 profile surface 缺失导致页面不可用。

## Rollback suggestion
- `git restore frontend/apps/web/src/pages/ContractFormPage.vue`

## Next suggestion
- 进入前端联调验证批：抽样验证 create/edit/readonly 三态下 header/actions/x2many 行为是否符合预期。
