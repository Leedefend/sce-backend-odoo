# 自定义前端对齐矩阵 v1（Batch A）

## 范围与原则
- 对齐对象：`project` / `task` / `budget` / `cost` / `payment` / `settlement`
- 真相源：原生业务页与既有原生闭环验收结果（`docs/ops/project_org_isolation_acceptance_v1.md`）
- 本轮仅做对齐审计，不新增业务事实，不在前端做权限补丁。

## 前端通用能力基线（证据）
- 通用路由存在：`/a/:actionId`（列表动作）、`/f/:model/:id`（表单）`frontend/apps/web/src/router/index.ts:85`
- 列表创建入口受后端权限契约控制：`contractRights.create` 决定是否显示“新建记录”`frontend/apps/web/src/views/ActionView.vue:1713`
- 表单保存走统一 `create/write`，并由 `canSave`（权限+runtime）门禁`frontend/apps/web/src/pages/ContractFormPage.vue:469`
- 不可写/只读由 scene contract runtime 驱动，不做前端业务特判`frontend/apps/web/src/pages/ContractFormPage.vue:459`

## 对齐矩阵
| 对象 | 原生是否已成立 | 前端列表/表单 | 前端创建/编辑 | 不可见/不可写处理 | 当前差异点 |
|---|---|---|---|---|---|
| `project.project` | 已成立（项目岗位+成员+闭环） | 有：项目驾驶舱与立项入口 + 通用表单 `frontend/apps/web/src/views/ProjectsIntakeView.vue:54` | 有：新建/编辑路径完整（通用 + 项目特化） | 有：由 contract rights/runtime 驱动只读与失败提示 | 低差异，Batch B 以回归为主 |
| `project.task` | 已成立（PM/成员可办，outsider deny） | 有：通用 action/list+form；`MyWork` 有任务入口 `frontend/apps/web/src/views/MyWorkView.vue:770` | 有：通用 `create/write` 支持 | 有：contract rights 与服务端拒绝回传 | 缺少 task 专用办理视图编排，主要依赖通用容器 |
| `project.budget` | 已成立（最小办理+锚点） | 部分：未发现显式模型视图；依赖通用 action/form | 部分：通用支持可用，但无显式预算前端编排 | 有：通用门禁可覆盖 | 模型级前端显式入口不足，需 Batch B 补“可发现性” |
| `project.cost.ledger` | 已成立（最小办理+锚点） | 部分：有 dashboard `cost_entry` 交互 + 通用 form `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:158` | 部分：场景内可录入；通用编辑依赖 action/form | 有：通用门禁可覆盖 | 场景表单与通用表单双轨，需统一验收口径 |
| `payment.request` | 已成立（最小办理+outsider deny） | 部分：`MyWork` 有入口 + payment action API `frontend/apps/web/src/api/paymentRequest.ts:60` | 部分：动作执行能力有，列表/表单依赖通用 action/form | 有：动作可返回 blocked reason；通用拒绝可见 | 缺少 payment 最小办理的单独前端闭环脚本 |
| `sc.settlement.order` | 已成立（最小办理+outsider deny） | 部分：`MyWork` 有入口；未见专用 settlement API | 部分：依赖通用 action/form | 有：通用门禁可覆盖 | settlement 前端专用交互薄弱，需按最小办理补对齐 |

## Batch B 优先级（执行输入）
1. `project`：先做对齐回归（低风险、快收口）
2. `task`：补任务链路的前端办理证据（保持通用容器）
3. `budget/cost`：补显式入口与可发现性对齐（不改变业务语义）
4. `payment/settlement`：仅补最小办理链，不进入审批深链

## Batch B-1（project-slice）delta assessment
- 结论：`no-op`（无需新增前端模型特判；现有契约消费链已覆盖 project-slice 要求）。
- `list` 证据：列表创建入口受契约 `create` 权限控制，且走统一 action/list 容器 `frontend/apps/web/src/views/ActionView.vue:1713`。
- `form` 证据：表单渲染 profile 由 contract/runtime 决定（`create/edit/readonly`），禁止前端自定义权限推断 `frontend/apps/web/src/pages/ContractFormPage.vue:469`。
- `create` 证据：项目创建入口存在（`/f/project.project/new`），保存走统一 `createRecord` 路径 `frontend/apps/web/src/views/ProjectsIntakeView.vue:54`。
- `edit` 证据：编辑保存走统一 `writeRecord`，并按 `canSave` 门禁控制 `frontend/apps/web/src/pages/ContractFormPage.vue:3506`。
- `deny-path` 证据：`restricted/readonly` 由 scene runtime 下发并在前端呈现，不做模型补丁 `frontend/apps/web/src/pages/ContractFormPage.vue:421`。
- 模型特判风险检查：本批不新增 `project` 分支逻辑，仅复核既有契约消费行为（满足 `no-model-specific-branching-added`）。

## Batch B-2（task-slice）delta assessment
- 结论：`no-op`（无需新增 task 模型特判、专用组件或表单行为改写）。
- 通用路径证据：
  - action 列表入口采用通用 `'/a/:actionId'` 路由，`project.task` 通过 action contract 进入该通用路径 `frontend/apps/web/src/router/index.ts:75`。
  - 表单入口采用通用 `'/f/:model/:id'` 路由，`project.task` 作为 model 参数消费同一渲染链 `frontend/apps/web/src/router/index.ts:76`。
- list/form/create/edit/deny 证据：
  - list create 入口由契约 `create` 权限控制，不做 task 补丁 `frontend/apps/web/src/views/ActionView.vue:1713`。
  - form 读写门禁由 `canSave + sceneRuntimePageStatus` 决定，契约驱动只读/受限显示 `frontend/apps/web/src/pages/ContractFormPage.vue:505`。
  - create/edit 走统一 `createRecord/writeRecord`，无 task 专用保存逻辑 `frontend/apps/web/src/pages/ContractFormPage.vue:3515`。
  - deny-path 由 runtime 下发 restricted/readonly，前端仅展示 `frontend/apps/web/src/pages/ContractFormPage.vue:421`。
- stage change / outsider deny 与原生一致性证据：
  - `native_business_fact_native_operability_closure_verify.py` 复跑 PASS，包含 task create/edit/stage 与 outsider deny（`outsider_task_count=0`）。
- MyWork / Project 内入口检查（仅检查跳转）：
  - `MyWork` 对 `project.task` 标识“进入任务/处理项目任务”且走现有导航链 `frontend/apps/web/src/views/MyWorkView.vue:770`。
- `useActionViewNavigationRuntime` 仅对 `project.project` 有既有分支，未对 task 引入新分支 `frontend/apps/web/src/app/action_runtime/useActionViewNavigationRuntime.ts:52`。

## Batch B-3（budget/cost-slice）delta assessment
- 结论：`no-op`（在当前约束下不引入 budget/cost 模型特判与专用组件，保持契约消费链）。
- 通用路径证据：
  - budget/cost 仍走通用 action 与 form 路由（`/a/:actionId`、`/f/:model/:id`），不需要前端模型分支。
  - `frontend/apps/web/src/router/index.ts:75`
  - `frontend/apps/web/src/router/index.ts:76`
- list/form/create/edit/deny 证据：
  - list create 入口受契约 `create` 权限统一控制 `frontend/apps/web/src/views/ActionView.vue:1713`。
  - form 写入门禁由 `canSave + runtime status` 统一控制 `frontend/apps/web/src/pages/ContractFormPage.vue:505`。
  - 通用 create/edit 提交分别走 `createRecord/writeRecord` `frontend/apps/web/src/pages/ContractFormPage.vue:3515`。
  - deny-path 仍由 `restricted/readonly` runtime 状态下发并前端展示 `frontend/apps/web/src/pages/ContractFormPage.vue:421`。
- cost 场景内最小办理入口证据（不新增组件）：
  - `ProjectManagementDashboardView` 已存在 `cost_entry` 表单与提交按钮 `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:158`。
  - 点击提交触发 `submitCostEntry` 并走既有 intent 提交链，不改表单行为 `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:1260`。
- native 一致性证据：
  - 复跑 `native_business_fact_native_operability_closure_verify.py` PASS，包含 budget/cost create 成功与 outsider deny（`outsider_budget_count=0`, `outsider_cost_count=0`）。
- 差异说明：
  - budget/cost 的“可发现性”仍以通用 action/form 与场景区块为主；本批不改导航结构，仅记录为后续 Batch C 体验验收关注点。

## Batch B-4（payment/settlement-slice）delta assessment
- 结论：`no-op`（保持最小办理范围，不扩审批深链，不新增模型特判）。
- 通用路径证据：
  - payment/settlement 仍复用通用 action 与 form 路由：`/a/:actionId`、`/f/:model/:id`。
  - `frontend/apps/web/src/router/index.ts:75`
  - `frontend/apps/web/src/router/index.ts:76`
- list/form/create/edit/deny 证据：
  - list/form 创建编辑门禁沿用统一 contract/runtime 链：`ActionView` 的 `contractRights.create` 与 `ContractFormPage` 的 `canSave`。
  - `frontend/apps/web/src/views/ActionView.vue:1713`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:505`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:3515`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:3506`
- payment 最小办理前端入口证据：
  - `MyWork` 对 `payment.request` 提供“查看付款申请/处理付款申请”语义入口。
  - `frontend/apps/web/src/views/MyWorkView.vue:767`
  - 既有 payment action API（available/execute）可消费后端动作契约。
  - `frontend/apps/web/src/api/paymentRequest.ts:60`
- settlement 最小办理前端入口证据：
  - `MyWork` 对 `sc.settlement.order` 提供“查看结算事项/处理结算事项”语义入口。
  - `frontend/apps/web/src/views/MyWorkView.vue:769`
  - `ProjectManagementDashboardView` 已有 settlement summary 承载，不引入新组件。
  - `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:243`
- native 一致性证据：
  - 复跑 `native_business_fact_payment_settlement_operability_verify.py` PASS，`outsider_payment_count=0`、`outsider_settlement_count=0`。
- 差异说明：
  - settlement 前端“专用动作 API”薄于 payment（当前主要依赖通用 form/action + summary）；本批按约束仅记录差异，不扩深层审批链。

## Batch C（前端最小办理链一致性收口）
- 验证链路：`project -> task -> budget/cost -> payment/settlement`。
- 一致性证据：
  - `native_business_fact_native_operability_closure_verify.py` PASS（project/task/budget/cost create-edit-stage + outsider deny）
  - `native_business_fact_payment_settlement_operability_verify.py` PASS（payment/settlement minimum operability + outsider deny）
- 前端判定：
  - 前端在上述对象上继续复用通用 action/form 与既有场景入口，未引入模型特判或权限补丁。
  - 闭环结论：前端最小办理链与原生闭环基线一致，`frontend alignment acceptance v1` 达成。

## 差异判定规则（用于 Batch C）
- 若原生闭环已 PASS，但前端失败：先判定为前端消费/编排问题。
- 若前端与原生都失败：再回溯后端事实/权限证据。
- 禁止前端通过模型特判“绕过”后端权限与办理语义。
