# Product Scene Template v1（Phase 12-B）

## 目标
- 将首产品场景从“实现样例”沉淀为“可复用模板”。
- 固定 scene/capability/intent/contract/suggested_action/post_action/role behavior 的最小规范。

## 模板骨架

### 1) Scene
- `scene_key`: `<domain>.<action>`（示例：`project.initiation`）
- `route`: `/s/<scene_key>`
- `target.menu_xmlid`: 必填
- `target.action_xmlid`: 建议

### 2) Capability
- `capability_key`: `<domain>.<action>.enter`
- `app`: 对应业务 app（示例：`project_management`）
- `scene_key`: 与上面一致
- `required_roles`: 明确列举

### 3) Intent
- 主入口 intent：`<domain>.<action>.enter`
- 输入：最小创建字段（必须字段 + 可选字段）
- 输出：
  - `state`（`ready|success|denied`）
  - `record`（创建成功时）
  - `suggested_action`
  - `suggested_action_payload`
  - `contract_ref`

### 4) Contract
- 一级：`ui.contract(op=menu, menu_id/menu_xmlid)`
- 二级：`ui.contract(op=model, model)`（仅 menu 不可用时）
- `suggested_action_payload` 与 `contract_ref` 必须统一入口

### 5) Suggested Action
- 成功态：不得返回 fallback 动作（如 `open_workbench`）
- 拒绝态：允许 `request_access`/`fix_input` 等 contract-safe 提示

### 6) Post Action
- 成功后可直接回读契约或导航到 scene-ready 页面
- 失败后必须可诊断（`error.code` 必填）

### 7) Role Behavior
- 每个角色明确 `open`/`create` 行为预期
- 无权限行为必须 contract-safe，不得 500

## 与 `project.initiation` 一致性核对
- Scene：`project.initiation` 已落地
- Capability：`project.initiation.enter` 已落地
- Intent：`project.initiation.enter` 已落地
- Contract：`ui.contract` menu-first 已落地
- Suggested Action：成功态返回非 fallback 动作
- Role Behavior：由 `verify.product.project_initiation.roles` 冻结验证

结论：`project.initiation` 满足 Product Scene Template v1 的最小规范。

