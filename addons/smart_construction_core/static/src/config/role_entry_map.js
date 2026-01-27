/** @odoo-module **/

export const ROLE_ENTRY_MAP = [
  {
    key: "project_work",
    label: "项目工作",
    icon: "P",
    desc: "项目看板与概览入口",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_project_project",
      action_xmlid: "smart_construction_core.action_sc_project_kanban_lifecycle",
    },
    quick_actions: [
      { label: "新建项目", action_xmlid: "smart_construction_core.action_project_initiation" },
      { label: "项目看板", action_xmlid: "smart_construction_core.action_project_dashboard" },
    ],
  },
  {
    key: "capability_matrix",
    label: "能力矩阵",
    icon: "M",
    desc: "查看角色可用能力",
    default_action: {
      menu_xmlid: "smart_construction_portal.menu_sc_portal_capability_matrix",
      action_xmlid: "smart_construction_portal.action_sc_portal_capability_matrix",
    },
    quick_actions: [],
  },
  {
    key: "contract_work",
    label: "合同工作",
    icon: "C",
    desc: "合同台账与合同清单",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_contract_income",
      action_xmlid: "smart_construction_core.action_construction_contract_my",
    },
    quick_actions: [
      { label: "收入合同", action_xmlid: "smart_construction_core.action_construction_contract_income" },
      { label: "支出合同", action_xmlid: "smart_construction_core.action_construction_contract_expense" },
    ],
  },
  {
    key: "cost_work",
    label: "成本工作",
    icon: "K",
    desc: "成本台账与预算入口",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_project_cost_ledger",
      action_xmlid: "smart_construction_core.action_project_cost_ledger_my",
    },
    quick_actions: [
      { label: "成本台账", action_xmlid: "smart_construction_core.action_project_cost_ledger" },
      { label: "项目预算", action_xmlid: "smart_construction_core.action_project_budget" },
    ],
  },
  {
    key: "finance_work",
    label: "财务工作",
    icon: "F",
    desc: "付款申请与财务台账",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_payment_request",
      action_xmlid: "smart_construction_core.action_payment_request_my",
    },
    quick_actions: [
      { label: "待我审批", action_xmlid: "smart_construction_core.action_sc_tier_review_my_payment_request" },
      { label: "资金台账", action_xmlid: "smart_construction_core.action_sc_treasury_ledger" },
    ],
  },
];
