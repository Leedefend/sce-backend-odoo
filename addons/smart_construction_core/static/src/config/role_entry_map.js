/** @odoo-module **/

export const ROLE_ENTRY_MAP = [
  {
    key: "project_work",
    label: "项目工作",
    icon: "P",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_project_project",
      action_xmlid: "smart_construction_core.action_sc_project_list",
    },
  },
  {
    key: "contract_work",
    label: "合同工作",
    icon: "C",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_contract_income",
      action_xmlid: "smart_construction_core.action_construction_contract_income",
    },
  },
  {
    key: "cost_work",
    label: "成本工作",
    icon: "K",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_sc_project_cost_ledger",
      action_xmlid: "smart_construction_core.action_project_cost_ledger",
    },
  },
  {
    key: "finance_work",
    label: "财务工作",
    icon: "F",
    default_action: {
      menu_xmlid: "smart_construction_core.menu_payment_request",
      action_xmlid: "smart_construction_core.action_payment_request",
    },
  },
];
