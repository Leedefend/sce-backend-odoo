# Sidebar Navigation Consumer Acceptance v1

## Scope

本清单用于验收 Sidebar 纯消费化结果，覆盖点击分发、高亮、展开、不可用拦截与 route 消费一致性。

## Checklist Mapping

1. 数据源只消费 `nav_explained`
   - Verify: `scripts/verify/sidebar_navigation_consumer_verify.py`

2. 前端禁止 `menu_id -> /m/:id` 回退拼接
   - Verify: `scripts/verify/sidebar_navigation_consumer_verify.py`
   - Verify: `scripts/verify/sidebar_route_consumer_ux_verify.py`

3. 目录节点仅展开/折叠，不触发跳转
   - Verify: `scripts/verify/sidebar_directory_rule_verify.py`
   - Verify: `scripts/verify/sidebar_interaction_smoke_verify.py`

4. unavailable 节点不可点击且有原因提示入口
   - Verify: `scripts/verify/sidebar_unavailable_guard_verify.py`
   - Verify: `scripts/verify/sidebar_interaction_smoke_verify.py`

5. active 高亮链路基于 `active_match`
   - Verify: `scripts/verify/sidebar_active_chain_verify.py`

6. 面包屑与角色快捷入口消费解释层 route
   - Verify: `scripts/verify/sidebar_route_consumer_ux_verify.py`

7. 统一点击分发器仍为 `navigateByExplainedMenuNode`
   - Verify: `scripts/verify/sidebar_navigation_consumer_verify.py`
   - Verify: `scripts/verify/sidebar_interaction_smoke_verify.py`

## Acceptance Commands

- `python3 scripts/verify/sidebar_navigation_consumer_verify.py`
- `python3 scripts/verify/sidebar_active_chain_verify.py`
- `python3 scripts/verify/sidebar_directory_rule_verify.py`
- `python3 scripts/verify/sidebar_unavailable_guard_verify.py`
- `python3 scripts/verify/sidebar_route_consumer_ux_verify.py`
- `python3 scripts/verify/sidebar_interaction_smoke_verify.py`
- `python3 scripts/verify/sidebar_acceptance_checklist_verify.py`

