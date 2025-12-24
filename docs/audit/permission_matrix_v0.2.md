# Permission Matrix v0.2

## 1. 范围与原则
- 范围：smart_construction_core（含依赖原生模块的桥接权限）
- 原则：
  - 菜单可见 ≠ 可操作（操作必须由 action groups / ACL / record rule 三层兜底）
  - CI bypass 仅用于测试环境，不能影响生产默认行为
  - “能力组（capability group）”是对外承诺，“原生组/隐式组”是实现细节

## 2. 角色定义（Role）
| Role | 说明 | 典型用户 |
|---|---|---|
| Super Admin | 超级管理员，拥有所有权限 | 系统实施/开发者 |
| Platform Admin / IT | 平台管理员，负责系统配置与维护 | IT 运维 |
| Project Manager | 项目经理，负责项目全过程管理 | 项目部负责人 |
| Finance Manager | 财务经理，负责财务审批与管理 | 财务部负责人 |
| Finance User | 财务经办，负责日常财务操作 | 出纳、会计 |
| Readonly / Auditor | 审计/只读，只查看数据 | 审计人员、管理层 |

## 3. 能力组定义（Capability Groups）
| Capability Group | 含义 | implied_ids / 依赖 | 关键对象 |
|---|---|---|---|
| `group_sc_internal_user` | SC 内部用户 | `base.group_user` | 内部用户身份 |
| `group_sc_super_admin` | SC 超级管理员 | 所有 `manager` 级能力组 | 运维/开发 |
| | | | |
| `group_sc_bridge_project_read` | **桥接组**-项目只读 | `project.group_project_user` | project.project, project.task |
| | | | |
| `group_sc_cap_project_read` | **能力组**-项目只读 | `group_sc_bridge_project_read` | project.project |
| `group_sc_cap_project_user` | **能力组**-项目经办 | `group_sc_cap_project_read` | project.task |
| `group_sc_cap_project_manager` | **能力组**-项目审批 | `group_sc_cap_project_user` | project.project |
| | | | |
| `group_sc_cap_finance_read` | **能力组**-财务只读 | `group_sc_internal_user` | account.move |
| `group_sc_cap_finance_user` | **能力组**-财务经办 | `group_sc_cap_finance_read` | sc.payment.request |
| `group_sc_cap_finance_manager` | **能力组**-财务审批 | `group_sc_cap_finance_user` | sc.payment.request |
| | *... (其他能力组，如合同、成本、物资等)* | | |

## 4. 动作域（Actions Domains）
- D1 Settings/Config
- D2 Master Data (journals, incoterms, etc.)
- D3 Project
- D4 Contract
- D5 Finance
- D6 Stock/Purchase
- D7 Workflow/Tier
- D8 Tools/Diagnostics
> 每个域给出“可见入口（menu）/可执行动作（action/server action）/数据访问（ACL+RR）”三张表

## 5. 矩阵（Role × Domain × Capability）
### 5.1 总览矩阵
| Role \ Domain | D1 | D2 | D3 | D4 | D5 | D6 | D7 | D8 |
|---|---|---|---|---|---|---|---|---|

### 5.2 细化矩阵（逐域）
#### D5 Finance
| Role | Menu | Actions | Models (ACL) | Record Rules | 备注 |
|---|---|---|---|---|---|
| **Finance Manager** | `财务中心`<br>`待我审批` | `action_sc_finance_dashboard`<br>`action_sc_tier_review_my_payment_request` | `payment.request` (CRUD)<br>`construction.contract` (R)<br>`project.contract` (R) | 默认：继承系统规则 | 拥有财务域全部权限，包括审批 |
| **Finance User** | `财务中心` | `action_sc_finance_dashboard` | `payment.request` (CRU-)<br>`construction.contract` (R)<br>`project.contract` (R) | 默认：继承系统规则 | 可创建/读/写，不可删除 |
| **Readonly / Auditor** | `财务中心` | `action_sc_finance_dashboard` | `payment.request` (R)<br>`construction.contract` (R)<br>`project.contract` (R) | 默认：继承系统规则 | 仅只读访问 |

## 6. 风险清单与保底策略

**高风险动作的判定规则：** 满足以下任一条件的动作，必须拥有显式的 `groups_id` 定义。
1.  属于 Settings/Config（会改变系统行为）
2.  涉及 Master Data/财务账套（journals、tax、incoterms 等）
3.  属于 server action / automation / mass action（能批量影响数据）
4.  涉及导入/导出/删除/重建（不可逆或大范围影响）

### 高风险动作清单 (Top 20)

| Rank | XML ID | Model | 名称/用途 | 风险原因 | 应归属 groups |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `base_setup.action_general_configuration` | `ir.actions.act_window` | 通用设置 | Settings | `group_sc_super_admin` |
| 2 | `account.action_account_config` | `ir.actions.act_window` | 财务设置 | Settings | `group_sc_super_admin` |
| 3 | `stock.action_stock_config_settings` | `ir.actions.act_window` | 库存设置 | Settings | `group_sc_super_admin` |
| 4 | `project.project_config_settings_action`| `ir.actions.act_window` | 项目设置 | Settings | `group_sc_super_admin` |
| 5 | `purchase.action_purchase_configuration`| `ir.actions.act_window` | 采购设置 | Settings | `group_sc_super_admin` |
| 6 | `account.action_account_journal_form` | `ir.actions.act_window` | 会计科目 | Master Data | `group_sc_cap_finance_manager` |
| 7 | `account.action_incoterms_tree` | `ir.actions.act_window` | 国际贸易术语 | Master Data | `group_sc_cap_finance_manager` |
| 8 | `action_sc_workflow_def` | `ir.actions.act_window` | 工作流定义 | Settings | `group_sc_cap_config_admin` |
| 9 | `base.action_module_upgrade` | `ir.actions.server` | 模块升级 | Server Action | `group_sc_super_admin` |
| 10 | `base_import.action_import_data` | `ir.actions.client` | 导入数据 | Import/Delete | `group_sc_super_admin` |
| 11 | `action_project_boq_import_wizard` | `ir.actions.act_window`| BOQ 导入 | Import/Delete | `group_sc_cap_cost_manager` |
| 12 | `action_quota_import_wizard` | `ir.actions.act_window` | 定额库导入 | Import/Delete | `group_sc_cap_config_admin` |
| 13 | `stock.action_replenishment` | `ir.actions.server` | 库存补货 | Mass Action | `stock.group_stock_user` |
| 14 | `server_action_material_plan_tier_approved` | `ir.actions.server`| 物资计划审批 | Server Action |`group_sc_cap_material_manager`|
| 15 | `server_action_payment_request_on_approved` |`ir.actions.server` | 付款申请审批 | Server Action |`group_sc_cap_finance_manager` |
| 16 | `action_project_cost_code` | `ir.actions.act_window` | 成本科目 | Master Data | `group_sc_cap_config_admin`|
| 17 | `action_project_dictionary_discipline`| `ir.actions.act_window` | 专业字典 | Master Data | `group_sc_cap_data_read` |
| 18 | `digest.digest_digest_action` | `ir.actions.act_window` | 摘要邮件 | Settings | `group_sc_super_admin` |
| 19 | `action_sc_project_document` | `ir.actions.act_window` | 项目文档 | Data Access | `group_sc_cap_project_read`|
| 20 | `db_reset` (Makefile) | `n/a` | 数据库重置 | Import/Delete | 运维动作，非 Odoo Action |

- 关键模型无菜单但要可选（例如财务选合同）
- 升级兼容策略（避免 patch 覆盖原生升级）

## 7. 变更记录
- v0.2: 文档骨架建立，并完成 D5 Finance 域的权限梳理示范。

---

### v0.2 Done 条件
- [x] 至少 6 个角色已定义
- [x] 至少 8 个 Domain 已列出（可空表）
- [x] 至少 1 个 Domain（D5）有完整示范（menu/action/ACL/RR）
- [x] 给出高风险动作清单（Top 20）
