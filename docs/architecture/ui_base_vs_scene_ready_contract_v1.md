# UI Base Contract vs Scene-ready Contract v1

## 目标

冻结三层契约口径，明确谁能直接给前端，谁只能作为编排输入。

## 边界定义

### 1) UI Base Contract

- 输入方：平台原生动作/视图解析产物（`ui_base_contract`，含 `views/fields/search/permissions/workflow/validator/actions`）。
- 输出方：`UI Base Contract Adapter`（当前实现：`addons/smart_core/core/ui_base_contract_adapter.py`）。
- 可被谁消费：仅 Scene Orchestrator/Compiler。
- 不可被谁消费：前端页面组件、页面路由层、渲染器。

### 2) Scene-ready Contract

- 输入方：`UI Base Contract Adapter` 输出的 `orchestrator_input` + scene profile/policy/provider。
- 输出方：`scene_ready_contract_v1`（当前实现：`addons/smart_core/core/scene_ready_contract_builder.py`）。
- 可被谁消费：前端页面（list/form/workspace）、导航/动作/搜索/权限展示层。
- 不可被谁消费：领域业务规则层（Domain）反向写入。

### 3) App Shell Contract

- 输入方：system.init 运行时聚合（用户、导航、角色、能力、治理元数据）。
- 输出方：App Shell 初始化载荷（`nav/default_route/role_surface/capabilities/meta`）。
- 可被谁消费：壳层路由、导航容器、全局状态。
- 不可被谁消费：页面结构渲染细节（`zones/blocks/search_surface`）。

## 禁止直连规则

- 前端禁止读取 `ui.contract.views.*`、`ui.contract.search`、`ui.contract.permissions` 作为页面结构输入。
- 前端页面只可读取 scene-ready 子结构：`blocks/actions/search_surface/permission_surface/workflow_surface/validation_surface`。

