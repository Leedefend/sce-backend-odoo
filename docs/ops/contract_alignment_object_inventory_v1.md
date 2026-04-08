# Contract Alignment Acceptance v1 · Batch A 对象盘点

## 盘点范围
- 对象：`project.project` / `project.task` / `project.budget` / `project.cost.ledger` / `payment.request` / `sc.settlement.order`
- 合同面：`list` / `form` / `rights` / `runtime`
- 目标：形成三层字段视图
  - 稳定字段（当前阶段应视为稳定）
  - 差异字段（对象/场景存在差异）
  - 前端真实依赖字段（当前消费链实际读取）

## Contract 通用骨架（跨对象）
- `ui.contract` 入口参数骨架（`op/action_id/model/view_type/render_profile/contract_surface`）
  - `frontend/apps/web/src/api/contract.ts:13`
- 列表创建门禁依赖 `contractRights.create`
  - `frontend/apps/web/src/views/ActionView.vue:1713`
- 表单写入门禁依赖 `rights + scene runtime`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:505`
- 表单 profile 依赖 `render_profile`（`create/edit/readonly`）
  - `frontend/apps/web/src/pages/ContractFormPage.vue:469`

## 对象字段矩阵
| 对象 | list contract（稳定/差异/依赖） | form contract（稳定/差异/依赖） | rights contract（稳定/差异/依赖） | runtime contract（稳定/差异/依赖） |
|---|---|---|---|---|
| `project.project` | 稳定：`model,id,name,view_type`；差异：项目入口可走 intake/management；依赖：`create` 权限控制列表“新建” | 稳定：`fields,visible_fields,layout/render_profile`；差异：project create 页有 quick/standard intake；依赖：`createRecord/writeRecord` | 稳定：`rights.read/write/create/unlink`；差异：project 在 create 页更依赖 `create`；依赖：`canSave` | 稳定：`restricted/readonly` 页面态；差异：project create 后有 nextSceneRoute；依赖：save 后 scene/workbench refresh |
| `project.task` | 稳定：通用 `/a/:actionId` 承载；差异：MyWork 有 task 入口语义；依赖：列表点击进入通用 form | 稳定：通用 `/f/:model/:id` 与 `saveRecord`；差异：无 task 专用 form 逻辑；依赖：`writeRecord/createRecord` | 稳定：同通用 rights；差异：task 常在 non-project create/edit 混合场景使用；依赖：`rights + runtime` 双门禁 | 稳定：`readonly/restricted`；差异：task stage 通过表单字段写入体现；依赖：runtime 状态阻断不可写 |
| `project.budget` | 稳定：通用 list/action 承载；差异：前端显式入口弱；依赖：ActionView 通用 create 门禁 | 稳定：通用 form contract；差异：预算字段集合由 contract 返回决定；依赖：`createRecord/writeRecord` | 稳定：同通用 rights；差异：budget create 对 `create` 权限敏感；依赖：`canSave` | 稳定：restricted/readonly；差异：与 cost 联动场景常在 project dashboard；依赖：runtime 阻断 |
| `project.cost.ledger` | 稳定：通用 list/action；差异：dashboard 有 `cost_entry` block；依赖：列表或场景入口均回到 contract 提交链 | 稳定：通用 form + 场景 block；差异：`cost_entry` 默认值/提交文案来自 block payload；依赖：`date/amount/description/cost_code_id` | 稳定：同通用 rights；差异：cost 场景写入能力依赖 contract+capability；依赖：`canSave`/button disabled | 稳定：runtime 控制可写；差异：`cost.tracking` 场景 block key 排序；依赖：scene block payload |
| `payment.request` | 稳定：通用 list/action + MyWork 入口；差异：有专用 action API；依赖：`available_actions/execute` | 稳定：通用 form 支持；差异：payment 场景还可由 dashboard `paymentEntry` block 提交；依赖：`paymentEntryForm` 字段 | 稳定：rights 门禁；差异：payment 操作可由 action surface 额外约束；依赖：前端消费 `allowed/reason_code` | 稳定：restricted/readonly；差异：动作执行结果含 handoff/idempotency 元数据；依赖：执行后反馈展示 |
| `sc.settlement.order` | 稳定：通用 list/action + MyWork 入口；差异：暂无与 payment 对称的专用 API；依赖：通用入口可达 | 稳定：通用 form contract；差异：dashboard 主要消费 `settlement_summary`；依赖：通用 create/edit 提交 | 稳定：rights 门禁；差异：多依赖通用 contract 而非独立动作面；依赖：`canSave` | 稳定：runtime 页面态；差异：settlement 场景当前以 summary 为主；依赖：summary block payload |

## 前端真实依赖字段（冻结候选）
- list 关键依赖：`model`, `id`, `name`, `permissions.effective.rights.create`, `head.view_type`
- form 关键依赖：`fields`, `visible_fields`, `render_profile`, `permissions.effective.rights.*`
- runtime 关键依赖：`scene contract permissions(can_create/can_edit)`, `page_status(restricted/readonly)`
- action 关键依赖（payment 侧）：`actions[].allowed/reason_code/execute_intent/execute_params`

## Batch B/C/D 输入清单
- Batch B（contract-native）：核对 `create/edit/readonly/restricted/deny-path` 语义与原生规则结果一致性。
- Batch C（contract-frontend）：核对上述“冻结候选依赖字段”是否被真实消费，识别前端兜底掩盖点。
- Batch D（freeze）：把“冻结候选依赖字段”固化到 `contract_freeze_surface_v1.md`，并标注变更门禁规则。
