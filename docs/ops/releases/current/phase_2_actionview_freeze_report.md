# Phase 2 ActionView Freeze Report

## Scope

- 目标：冻结 `ActionView` 的 Phase 2 结果，停止继续细拆，转入首发切片驱动。
- 证据输入：
  - `docs/ops/releases/current/phase_2_a_actionview_runtime_split_boundary.md`
  - `docs/ops/releases/current/phase_2_b_actionview_state_host_boundary.md`
  - `docs/architecture/actionview_runtime_hotspot_map_v1.md`
  - `docs/architecture/frontend_architecture_violation_inventory_v1.md`

## Batch-A / Batch-B 完成范围

### Batch-A

- `load dispatch runtime` 已从页面外移：
  - `frontend/apps/web/src/app/action_runtime/useActionViewLoadDispatchRuntime.ts`
- `action effects facade` 已独立：
  - `frontend/apps/web/src/app/action_runtime/useActionViewActionEffectsRuntime.ts`
- `batch effects facade` 已独立：
  - `frontend/apps/web/src/app/action_runtime/useActionViewBatchEffectsRuntime.ts`
- `advanced rows` 已进入 assembler：
  - `frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts`

### Batch-B

- `HUD entries` 已进入 assembler：
  - `frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts`
- `selection state` 已进入 runtime capsule：
  - `frontend/apps/web/src/app/runtime/actionViewSelectionRuntimeState.ts`
- `batch state` 已进入 runtime capsule：
  - `frontend/apps/web/src/app/runtime/actionViewBatchRuntimeState.ts`
- `group state` 已形成 capsule，页面只剩 bridge：
  - `frontend/apps/web/src/app/runtime/actionViewGroupRuntimeState.ts`
  - `frontend/apps/web/src/views/ActionView.vue`

## 当前状态归宿

### Assembler

- `advanced rows`
- `hud entries`
- 页面展示 VM 装配入口

核心载体：
- `frontend/apps/web/src/app/assemblers/action/useActionPageModel.ts`

### Runtime Capsule

- `selection`
- `batch`
- `group state`

核心载体：
- `frontend/apps/web/src/app/runtime/actionViewSelectionRuntimeState.ts`
- `frontend/apps/web/src/app/runtime/actionViewBatchRuntimeState.ts`
- `frontend/apps/web/src/app/runtime/actionViewGroupRuntimeState.ts`

### Page Shell

- 核心 load 数据面：
  - `status`
  - `traceId`
  - `lastTraceId`
  - `records`
  - `listTotalCount`
  - `projectScopeTotals`
  - `projectScopeMetrics`
- route / lifecycle / group bridge

核心载体：
- `frontend/apps/web/src/views/ActionView.vue`

## Page Shell 剩余字段分类

### A. 合法 Page Shell 职责

- `status / traceId / lastTraceId`
  - 原因：属于 load 生命周期与诊断锚点，当前直接服务页面状态切换与错误显示。
- `records / listTotalCount`
  - 原因：属于页面主数据面，当前仍是 list / kanban / advanced 三态渲染的共同输入。
- `projectScopeTotals / projectScopeMetrics`
  - 原因：属于页面主数据面摘要，当前和 records 装配路径绑定，继续外移不会直接提升首发切片边界。
- `route / lifecycle / group bridge`
  - 原因：属于 page shell 桥接面，直接连接路由、生命周期和 group drilldown。

### B. 后续可优化，作为 Batch-C 候选但本轮不展开

- `records / listTotalCount` 的进一步 host 下沉
- `projectScopeTotals / projectScopeMetrics` 的摘要归宿再收敛
- `group bridge` 从 page shell 继续变薄

### C. 潜在越层，需标注但本轮接受

- 页面在 assembler 之前仍要汇总部分 load 输入与 route bridge
- group runtime 的 route/drilldown bridge 仍由 page shell 承担

结论：
- 这些残留不再属于“前端业务推导逻辑”
- 它们是 page shell 厚度问题，不阻断首发切片

## Violation Inventory 更新摘要

- `ActionView` 相关问题已从“必须继续拆的当前主线”降级为“冻结接受 + backlog 管理”：
  - `State center still retained in page shell` -> `accepted`
  - `Page assembly not final` -> `backlog`
  - `Group runtime bridge still page-owned` -> `backlog`

详见：
- `docs/architecture/frontend_architecture_violation_inventory_v1.md`

## 验证引用

- `make verify.frontend.typecheck.strict`
- `make verify.product.final_slice_readiness_audit`
- `make verify.architecture.orchestration_platform_guard`
- `make verify.architecture.five_layer_workspace_audit`

本轮冻结结果：

- `make verify.product.final_slice_readiness_audit` -> `READY_FOR_SLICE`
  - 产物：`artifacts/backend/final_slice_readiness_audit.json`
- `make verify.architecture.orchestration_platform_guard` -> `PASS`
- `make verify.architecture.five_layer_workspace_audit` -> `PASS`

说明：

- `frontend.typecheck.strict` 在 Batch-A / Batch-B 执行过程中已持续通过。
- 本轮冻结没有继续改 `ActionView` 运行时代码，因此未再次展开内部拆分型验证。

## 为什么现在可以冻结

- `ActionView` 已不再掌握 `load/action/batch` 三条主链的总控权。
- 展示派生与交互基础状态已经从页面抽离到 assembler/capsule。
- 页面残留已被清楚归类为：
  - 合法 bridge
  - 主数据面 host
  - 后续可优化项
- 继续拆分不会直接提升“项目创建 -> 驾驶舱”首发切片的结构冻结收益。

## 冻结结论

- 结论：`ActionView` Phase 2 可以冻结。
- 管理口径：
  - 停止以 `ActionView` 为主线继续投入。
  - 除非后续首发切片被它直接阻断，否则不打开 Batch-C。
