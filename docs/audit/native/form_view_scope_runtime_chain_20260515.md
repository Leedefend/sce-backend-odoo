# 表单视图作用域运行链路梳理

## 目标

把“用户打开了哪个表单”这件事固定成可追踪链路，避免字段策略、低代码、模型默认视图混在一起。

## 打开链路

1. 前端路由读取：
   - `action_id`
   - `view_id` / `viewId`
   - `menu_id`
   - `record_id`
2. `ContractFormPage` 和 `RecordView` 优先调用 `loadActionContractRaw(action_id, ...)`。
3. 若动作契约不可用或动作模型与当前模型不一致，才退回 `loadModelContractRaw(model, ...)`。
4. `loadActionContractRaw` 与 `loadModelContractRaw` 都必须把显式 `view_id` 传给 `ui.contract.v2`。
5. `ui.contract.v2` 调用 `ui.contract`，并保留 `action_id/view_id`。
6. `ui.contract` / `PageAssembler` 将上下文写入 `contract_action_id/contract_view_id`。
7. `app.view.config._projection_identity` 产出三类结构事实身份：
   - `generic:{model}:{view_type}`
   - `view:{view_id}:{model}:{view_type}`
   - `action:{action_id}:{model}:{view_type}:view:{view_id}`
8. `app.view.config._safe_get_view_data` 用 Odoo `get_view(view_id=..., view_type=...)` 加载原生运行态 arch。
9. `PageAssembler._inject_current_form_settings_action` 只在有当前 `action_id` 时开放低代码表单设置。
10. 低代码字段策略写入 `model/action_id/view_id/company_id`，不写 `user_id`。

## 关键判定

- 有 `action_id`：这是动作专用页面，字段策略默认落动作 scope。
- 有显式 `view_id`：这是指定原生视图事实，必须传到后端并进入 projection identity。
- 没有 `action_id`：只能是模型默认视图，不开放当前动作低代码设置。
- 有 `user_id`：只能代表偏好，不得参与结构事实或字段策略。

## 本轮补齐

- 前端 `LoadActionContractOptions` / `LoadModelContractOptions` 增加 `viewId`。
- `ContractFormPage.loadContract()` 从路由读取 `view_id/viewId` 并传给 action/model 契约加载。
- `RecordView` 从路由读取 `view_id/viewId`，传给 action 契约加载，并在 action/view 路由上下文变化时重新加载。
- 新增运行链路 guard，确保显式 view 不会在前端 API 层丢失。
