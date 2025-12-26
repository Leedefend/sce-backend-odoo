# -*- coding: utf-8 -*-

# 权限矩阵单一事实源（可被测试读取生成用例）
# 每个角色定义：
# - groups: 赋予用户的组
# - menus_allow / menus_deny: 期望可见/不可见的菜单 xmlid
# - actions_allow / actions_deny: 期望可访问/不可访问的 action xmlid

PERM_MATRIX = {
    "super_admin": {
        "groups": ["smart_construction_core.group_sc_super_admin"],
        "menus_allow": [
            "smart_construction_core.menu_sc_root",
            "smart_construction_core.menu_sc_project_center",
            "smart_construction_core.menu_sc_finance_center",
            "smart_construction_core.menu_sc_contract_center",
        ],
        "menus_deny": [],
        "actions_allow": [
            "smart_construction_core.action_project_dashboard",
            "smart_construction_core.action_payment_request",
            "smart_construction_core.action_construction_contract",
            "smart_construction_core.action_sc_workflow_def",
        ],
        "actions_deny": [],
    },
    "project_read": {
        "groups": ["smart_construction_core.group_sc_cap_project_read"],
        "menus_allow": ["smart_construction_core.menu_sc_project_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_project_dashboard"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "project_manager": {
        "groups": ["smart_construction_core.group_sc_cap_project_manager"],
        "menus_allow": ["smart_construction_core.menu_sc_project_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_project_wbs"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "finance_read": {
        "groups": ["smart_construction_core.group_sc_cap_finance_read"],
        "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
        "menus_deny": ["smart_construction_core.menu_sc_project_center"],
        "actions_allow": ["smart_construction_core.action_payment_request"],
        "actions_deny": ["smart_construction_core.action_project_wbs"],
    },
    "finance_user": {
        "groups": ["smart_construction_core.group_sc_cap_finance_user"],
        "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
        "menus_deny": ["smart_construction_core.menu_sc_project_center"],
        "actions_allow": ["smart_construction_core.action_payment_request"],
        "actions_deny": ["smart_construction_core.action_project_material_plan"],
    },
    "finance_manager": {
        "groups": ["smart_construction_core.group_sc_cap_finance_manager"],
        "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
        "menus_deny": ["smart_construction_core.menu_sc_project_center"],
        "actions_allow": ["smart_construction_core.action_sc_tier_review_my_payment_request"],
        "actions_deny": ["smart_construction_core.action_project_material_plan"],
    },
    "contract_user": {
        "groups": ["smart_construction_core.group_sc_cap_contract_user"],
        "menus_allow": ["smart_construction_core.menu_sc_contract_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_construction_contract"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "contract_manager": {
        "groups": ["smart_construction_core.group_sc_cap_contract_manager"],
        "menus_allow": ["smart_construction_core.menu_sc_contract_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_construction_contract"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "cost_manager": {
        "groups": ["smart_construction_core.group_sc_cap_cost_manager"],
        "menus_allow": ["smart_construction_core.menu_sc_project_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_project_cost_compare"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "material_manager": {
        "groups": ["smart_construction_core.group_sc_cap_material_manager"],
        "menus_allow": ["smart_construction_core.menu_sc_material_center"],
        "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
        "actions_allow": ["smart_construction_core.action_project_material_plan"],
        "actions_deny": ["smart_construction_core.action_payment_request"],
    },
    "config_admin": {
        "groups": ["smart_construction_core.group_sc_cap_config_admin"],
        "menus_allow": ["smart_construction_core.menu_sc_root"],
        "menus_deny": [],
        "actions_allow": ["smart_construction_core.action_sc_workflow_def"],
        "actions_deny": [],
    },
}
