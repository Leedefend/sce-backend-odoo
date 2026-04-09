# Sidebar Navigation Consumer v1

## 1. Input Source

Sidebar 仅消费后端解释层输出 `nav_explained`。

- Endpoint: `POST /api/menu/navigation`
- Consumer entry: `frontend/apps/web/src/composables/useNavigationMenu.ts`
- Sidebar render: `frontend/apps/web/src/layouts/AppShell.vue` + `frontend/apps/web/src/components/MenuTree.vue`

## 2. Sidebar No Longer Owns

Sidebar 不再负责：

- `action_type` 解析
- `scene_key` 推导
- `/s` `/a` `/native/action` route 拼接
- 可点击性推断

## 3. Click Rule

统一点击入口：`navigateByExplainedMenuNode(node)`。

- `is_clickable = false` -> 不跳转
- `target_type = directory` -> 仅展开/折叠
- `target_type = unavailable` -> 不跳转
- 其他可点击节点 -> 直接 `router.push(node.route)`

额外约束：

- 禁止前端 `menu_id -> /m/:id` 回退拼接
- 快捷入口与面包屑同样只消费解释层 `route`

## 4. Active Rule

高亮匹配只基于 `active_match` 与当前路由上下文：

优先级：

1. `active_match.menu_id`
2. `active_match.scene_key`
3. `active_match.action_id`
4. `active_match.route_prefix`

## 5. Parent Expansion Rule

- 通过 `activeMenuId` 反查祖先链
- 祖先链 key 自动写入 `menuExpandedKeys`
- 目录节点保持展开/折叠纯交互，不触发跳转

## 6. Adaptation Guidance

若后端解释层字段变更：

1. 先更新 `frontend/apps/web/src/types/navigation.ts`
2. 再更新 `useNavigationMenu` 归一化函数
3. 最后更新 `MenuTree` 与 `AppShell` 消费

## 7. Verification Gates

以下脚本作为 Sidebar 纯消费化的回归门禁：

- `python3 scripts/verify/sidebar_navigation_consumer_verify.py`
- `python3 scripts/verify/sidebar_active_chain_verify.py`
- `python3 scripts/verify/sidebar_directory_rule_verify.py`
- `python3 scripts/verify/sidebar_unavailable_guard_verify.py`

门禁目标：

- 防止前端恢复 `action/scene` 推理与 route 拼接
- 保证目录节点仅展开/折叠
- 保证 unavailable 节点不可点击
- 保证 active 链路继续基于后端 `active_match`
