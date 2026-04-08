# Contract Alignment Acceptance v1 · Batch C

## 目标
- 核对前端真实消费字段集合与当前 contract 面是否一致。
- 识别“前端兜底是否掩盖 contract 不规范”的风险，并给出 Batch D 冻结输入。

## 通用消费者与真实依赖
- 通用 list 消费（六对象共用）：
  - `head.model/model`、`head.view_type/view_type`、`permissions.effective.rights.create`（创建按钮门禁）
  - 证据：`frontend/apps/web/src/views/ActionView.vue:1330`, `frontend/apps/web/src/views/ActionView.vue:1713`
- 通用 form 消费（六对象共用）：
  - `head.permissions.*`、`permissions.effective.rights.*`、`render_profile`
  - scene runtime：`permissions.can_create/can_edit` + `runtime_page_status/page_status`
  - 证据：`frontend/apps/web/src/pages/ContractFormPage.vue:478`, `frontend/apps/web/src/pages/ContractFormPage.vue:496`, `frontend/apps/web/src/pages/ContractFormPage.vue:505`
- payment 额外 action 面消费：
  - `actions[].allowed/reason_code/execute_intent/execute_params`
  - 证据：`frontend/apps/web/src/api/paymentRequest.ts:9`, `frontend/apps/web/src/api/paymentRequest.ts:23`, `frontend/apps/web/src/api/paymentRequest.ts:58`

## 对象级依赖与风险分类
| 对象 | 前端真实依赖字段 | 兜底掩盖风险 | 结论 |
|---|---|---|---|
| `project.project` | 通用 list + form + runtime 字段集合 | 低：`rights` 缺失时默认 `true`，可能掩盖 contract 漏字段 | 一致（需冻结 rights 字段） |
| `project.task` | 通用 list + form + runtime 字段集合 | 低：同上 | 一致（需冻结 rights/runtime 字段） |
| `project.budget` | 通用 list + form + runtime 字段集合 | 低：同上 | 一致（需冻结 rights/runtime 字段） |
| `project.cost.ledger` | 通用 list + form + runtime 字段集合 | 低：同上 | 一致（需冻结 rights/runtime 字段） |
| `payment.request` | 通用字段 + payment action surface 字段 | 低-中：若 action 字段缺失，前端可退回通用 form，可能降低错误可见性 | 一致（需冻结 action surface 字段） |
| `sc.settlement.order` | 通用 list + form + runtime 字段集合 | 低：同通用路径 | 一致（需冻结 rights/runtime 字段） |

## 兜底掩盖点（本批识别）
- `rights` 默认放行为 `true`：
  - `frontend/apps/web/src/app/contractActionRuntime.ts:50`
  - `frontend/apps/web/src/app/contractActionRuntime.ts:55`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:481`
  - `frontend/apps/web/src/pages/ContractFormPage.vue:486`
- `view_type` 缺失可被 fallback 吸收：
  - `frontend/apps/web/src/app/contractActionRuntime.ts:65`
  - `frontend/apps/web/src/app/contractActionRuntime.ts:71`

结论：当前六对象未出现实质消费偏移，但存在“字段缺失被兜底吞掉”的通用风险，需要在 Batch D 通过冻结面约束来抑制。

## Batch D 冻结候选
- 必冻（通用）：
  - `head.permissions.read/write/create/unlink`
  - `permissions.effective.rights.read/write/create/unlink`
  - `render_profile`
  - `scene permissions.can_create/can_edit`
  - `scene runtime_page_status/page_status`
- 必冻（payment 专项）：
  - `actions[].allowed`
  - `actions[].reason_code`
  - `actions[].execute_intent`
  - `actions[].execute_params`
