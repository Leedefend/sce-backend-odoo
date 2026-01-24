/** @odoo-module **/

export const DOMAIN_NAV_MAP = [
  {
    key: "project_center",
    name_cn: "项目管理",
    icon: "P",
    sequence: 10,
    menu_xmlids: ["smart_construction_core.menu_sc_project_center"],
    menu_name_keywords: ["项目"],
  },
  {
    key: "contract_center",
    name_cn: "合同管理",
    icon: "C",
    sequence: 20,
    menu_xmlids: ["smart_construction_core.menu_sc_contract_center"],
    menu_name_keywords: ["合同"],
  },
  {
    key: "cost_center",
    name_cn: "成本管理",
    icon: "K",
    sequence: 30,
    menu_xmlids: ["smart_construction_core.menu_sc_cost_center"],
    menu_name_keywords: ["成本", "费用"],
  },
  {
    key: "material_center",
    name_cn: "物资管理",
    icon: "M",
    sequence: 40,
    menu_xmlids: ["smart_construction_core.menu_sc_material_center"],
    menu_name_keywords: ["物资", "采购"],
  },
  {
    key: "finance_center",
    name_cn: "财务账款",
    icon: "F",
    sequence: 50,
    menu_xmlids: ["smart_construction_core.menu_sc_finance_center"],
    menu_name_keywords: ["结算", "财务", "付款", "资金"],
  },
  {
    key: "data_center",
    name_cn: "数据分析",
    icon: "D",
    sequence: 65,
    menu_xmlids: ["smart_construction_core.menu_sc_data_center"],
    menu_name_keywords: ["数据", "指标", "投影"],
  },
  {
    key: "dashboard_center",
    name_cn: "看板中心",
    icon: "B",
    sequence: 55,
    menu_xmlids: ["smart_construction_core.menu_sc_projection_root"],
    menu_name_keywords: ["看板", "驾驶舱"],
  },
  {
    key: "settings",
    name_cn: "基础资料",
    icon: "S",
    sequence: 90,
    menu_xmlids: ["smart_construction_core.menu_sc_config_center"],
    menu_name_keywords: ["配置", "流程", "字典"],
  },
  {
    key: "other",
    name_cn: "其他",
    icon: "…",
    sequence: 9999,
    menu_xmlids: [],
    menu_name_keywords: [],
  },
];

export const DEFAULT_DOMAIN_KEY = "other";

export const PINNED_ENTRIES = [
  {
    key: "workbench",
    name: "工作台",
    icon: "W",
    action_xmlid: "smart_construction_core.action_sc_project_workbench",
    tag: "试点",
  },
  {
    key: "dashboard",
    name: "项目看板",
    icon: "B",
    menu_xmlid: "smart_construction_core.menu_sc_project_dashboard",
    tag: "试点",
  },
  {
    key: "todo",
    name: "待办中心",
    icon: "T",
    tag: "即将上线",
  },
];
