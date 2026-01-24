/** @odoo-module **/

export const DOMAIN_NAV_MAP = [
  {
    key: "project_center",
    name_cn: "项目中心",
    icon: "",
    sequence: 10,
    menu_xmlids: ["smart_construction_core.menu_sc_project_center"],
    menu_name_keywords: ["项目"],
  },
  {
    key: "contract_center",
    name_cn: "合同台账",
    icon: "",
    sequence: 20,
    menu_xmlids: ["smart_construction_core.menu_sc_contract_center"],
    menu_name_keywords: ["合同"],
  },
  {
    key: "cost_center",
    name_cn: "费用/成本",
    icon: "",
    sequence: 30,
    menu_xmlids: ["smart_construction_core.menu_sc_cost_center"],
    menu_name_keywords: ["成本", "费用"],
  },
  {
    key: "material_center",
    name_cn: "物资/采购",
    icon: "",
    sequence: 40,
    menu_xmlids: ["smart_construction_core.menu_sc_material_center"],
    menu_name_keywords: ["物资", "采购"],
  },
  {
    key: "finance_center",
    name_cn: "结算/财务",
    icon: "",
    sequence: 50,
    menu_xmlids: ["smart_construction_core.menu_sc_finance_center"],
    menu_name_keywords: ["结算", "财务", "付款", "资金"],
  },
  {
    key: "data_center",
    name_cn: "数据中心",
    icon: "",
    sequence: 60,
    menu_xmlids: [
      "smart_construction_core.menu_sc_data_center",
      "smart_construction_core.menu_sc_projection_root",
    ],
    menu_name_keywords: ["数据", "指标", "驾驶舱", "投影"],
  },
  {
    key: "settings",
    name_cn: "配置中心",
    icon: "",
    sequence: 90,
    menu_xmlids: ["smart_construction_core.menu_sc_config_center"],
    menu_name_keywords: ["配置", "流程", "字典"],
  },
  {
    key: "other",
    name_cn: "其他",
    icon: "",
    sequence: 99,
    menu_xmlids: [],
    menu_name_keywords: [],
  },
];

export const DEFAULT_DOMAIN_KEY = "other";
