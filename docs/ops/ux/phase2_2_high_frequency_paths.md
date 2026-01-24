# Phase 2.2 高频路径压缩

## Actions
- 我的项目：`smart_construction_core.action_sc_project_my_list`
- 项目列表：`smart_construction_core.action_sc_project_list`
- 合同工作（收入合同）：`smart_construction_core.action_construction_contract_income`
- 成本台账：`smart_construction_core.action_project_cost_ledger`
- 付款/收款申请：`smart_construction_core.action_payment_request`

## Filters
Search view: `smart_construction_core.view_project_project_search_my`

- `filter_my_projects`：我的项目（manager_id = uid）
- `filter_draft`：草稿（lifecycle_state = draft）
- `filter_in_progress`：进行中（lifecycle_state = in_progress）

## Role Entry Quick Actions
Config: `addons/smart_construction_core/static/src/config/role_entry_map.js`

- 项目工作：新建项目 / 项目看板
- 合同工作：收入合同 / 支出合同
- 成本工作：成本台账 / 项目预算
- 财务工作：待我审批 / 资金台账

## Rollback
- 角色入口层关闭：`sc_role_entries=0`
- role_entry_map 置空：不渲染
- 恢复菜单/域分组不受影响
