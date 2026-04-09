# Menu Target Interpreter Contract v1

## 1. Scope

本契约定义“菜单解释层（menu target interpreter）”输出。

- 输入：`menu_fact_layer_v1`（facts-only）
- 输出：`nav_explained`
- 目标：将每个菜单节点解释为唯一导航目标

## 2. Layer Boundary

解释层负责：

- 菜单节点目标类型解释（`target_type`）
- 交付方式解释（`delivery_mode`）
- route 统一生成
- active_match 统一生成
- unavailable 原因码输出

解释层不负责：

- 事实层扫描与 action 原始绑定写回
- route/scene/target 回写 facts-only
- 页面结构、视图布局、字段渲染契约
- Sidebar 样式与前端交互逻辑

## 3. Output Fields

每个解释节点包含：

- `menu_id`
- `key`
- `name`
- `is_visible`
- `is_clickable`
- `target_type`
- `delivery_mode`
- `route`
- `target`
- `active_match`
- `availability_status`
- `reason_code`
- `source`
- `children`

## 4. Enums

### `target_type`

- `directory`
- `scene`
- `action`
- `native`
- `url`
- `unavailable`

### `delivery_mode`

- `custom_scene`
- `custom_action`
- `native_bridge`
- `external_url`
- `none`

### `reason_code`

- `TARGET_MISSING`
- `ACTION_INVALID`
- `SCENE_UNRESOLVED`
- `DIRECTORY_ONLY`
- `DELIVERY_UNSUPPORTED`
- `PERMISSION_DENIED`

## 5. Interpretation Priority

1. 显式 scene 映射（menu/action/xmlid）
2. 可承接 `act_window` → `custom_action`
3. 可桥接 action → `native_bridge`
4. `act_url` → `external_url`
5. `directory` / `unavailable`

## 6. Route Generation

- scene: `/s/:scene_key?menu_id=:menu_id`
- action: `/a/:action_id?menu_id=:menu_id`
- native: `/native/action/:action_id?menu_id=:menu_id`
- url: `target.url`
- directory/unavailable: `null`

## 7. Active Match

- `menu_id` 始终输出
- scene 节点输出 `scene_key`
- action/native 节点输出 `action_id`
- 输出 `route_prefix` 供前端高亮匹配

