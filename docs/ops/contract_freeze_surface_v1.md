# Contract Freeze Surface v1

## Freeze scope
- 对象：`project.project` / `project.task` / `project.budget` / `project.cost.ledger` / `payment.request` / `sc.settlement.order`
- 目的：冻结当前前端最小依赖契约面，防止无审查变更导致可见性/可写性/动作语义漂移。

## Frozen fields (model-surface, mandatory)
- 权限字段（必须稳定输出）：
  - `head.permissions.read`
  - `head.permissions.write`
  - `head.permissions.create`
  - `head.permissions.unlink`
  - `permissions.effective.rights.read`
  - `permissions.effective.rights.write`
  - `permissions.effective.rights.create`
  - `permissions.effective.rights.unlink`
- 视图/渲染字段（必须稳定输出）：
  - `head.model` / `model`
  - `head.view_type` / `view_type`
  - `render_profile`

## Frozen fields (scene-runtime-extension-surface, conditional)
- 该层字段仅在 `ui.contract` 提供 `scene_contract_v1` 扩展分支时适用。
- 字段清单：
  - `permissions.can_create`
  - `permissions.can_edit`
  - `runtime_page_status` / `page_status`

适用说明：
- 以上字段的归属已在 `docs/ops/contract_runtime_surface_classification_screen_v1.md` 分类为 `scene_contract_v1` 扩展面，
  不再要求在 `op=model` 或 `page.contract/system.init` 根层强制出现。

## Frozen fields (payment action surface)
- `actions[].allowed`
- `actions[].reason_code`
- `actions[].execute_intent`
- `actions[].execute_params`

## Risk guard notes
- 若上述权限字段缺失，当前前端存在默认放行兜底风险：
  - `frontend/apps/web/src/app/contractActionRuntime.ts:55`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:486`
- 若 `view_type` 缺失，当前前端存在 fallback 吸收风险：
  - `frontend/apps/web/src/app/contractActionRuntime.ts:71`

## Change-control rule (mandatory)
- 任何冻结字段变更必须同时满足：
  - 提交 dedicated task contract（governance 类型）。
  - 在变更前更新本文件并标注影响对象与消费链。
  - 提供 contract-native 与 contract-frontend 双线回归证据。
  - 未通过证据门禁时，禁止合入。

## Out-of-scope
- 本文件不定义新业务语义。
- 本文件不替代 ACL/rule 或原生业务事实验证。
