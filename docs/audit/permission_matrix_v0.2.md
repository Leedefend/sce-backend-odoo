# Permission Matrix v0.3

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

## 4. Domain 全量清单
> 每个域的目标是给出“可见入口（menu）/可执行动作（action）/数据访问（models）”三张表。

### D1 Settings/Config
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_config_center` | `n/a` | 配置中心根入口（groups：`group_sc_cap_config_admin`） |
| Menu | `menu_project_quota_root` | `project.dictionary` | 定额库入口（配置子树，groups：`group_sc_cap_data_read`） |
| Action | `base_setup.action_general_configuration` | `res.config.settings` | 原生通用设置 |
| Action | `account.action_account_config` | `res.config.settings` | 财务设置 |
| Action | `stock.action_stock_config_settings` | `res.config.settings` | 库存设置 |
| Action | `project.project_config_settings_action` | `res.config.settings` | 项目设置 |
| Action | `purchase.action_purchase_configuration` | `res.config.settings` | 采购设置 |
| Action | `action_project_cost_code` | `project.cost.code` | 成本科目维护（仅 `group_sc_cap_config_admin`） |
| Action | `action_quota_import_wizard` | `quota.import.wizard` | 定额导入向导（仅 `group_sc_cap_config_admin`） |
| Action | `base.action_module_upgrade` | `ir.actions.server` | 模块升级（仅 `group_sc_super_admin`） |

### D2 Master Data
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_data_center` | `n/a` | 数据中心根入口（groups：`group_sc_cap_data_read`） |
| Menu | `menu_sc_dictionary` | `project.dictionary` | 业务字典入口 |
| Menu | `menu_project_quota_root` | `project.dictionary` | 定额库入口 |
| Action | `action_project_dictionary` | `project.dictionary` | 字典全量列表 |
| Action | `action_project_dictionary_discipline` | `project.dictionary` | 专业字典 |
| Action | `action_project_dictionary_sub_item` | `project.dictionary` | 定额子目（无菜单但被选为物资/成本引用） |
| Action | `action_project_quota_center` | `ir.actions.client` | 定额中心 client action |
| Model | `project.dictionary` | `project.dictionary` | 数据中心核心模型 |
| Model | `project.cost.code` | `project.cost.code` | 成本科目树，供成本/采购/预算引用 |

### D3 Project
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_project_center` | `n/a` | 项目中心主入口 |
| Action | `action_project_initiation` | `project.project` | 项目立项（仅 project user/manager） |
| Action | `project.open_view_project_all` | `project.project` | 项目列表 |
| Action | `action_project_dashboard` | `project.project` | 项目驾驶舱（跨域统计需额外 read 权限） |
| Action | `action_project_wbs` | `construction.work.breakdown` | 工程结构（预算/物资需要引用） |
| Action | `action_work_breakdown` | `construction.work.breakdown` | 工程结构（项目侧入口） |
| Action | `action_sc_project_structure` | `sc.project.structure` | 工程结构（清单 WBS 视图） |
| Model | `project.project` | `project.project` | 核心项目模型，强记录规则 |
| Model | `project.task` | `project.task` | 任务模型，继承项目记录规则 |

### D4 Contract
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_contract_center` | `n/a` | 合同中心根入口 |
| Menu | `menu_sc_contract_income` | `construction.contract` | 收入合同列表 |
| Menu | `menu_sc_contract_expense` | `construction.contract` | 支出合同列表 |
| Action | `action_construction_contract` | `construction.contract` | 全量合同列表（受 SC 合同组控制） |
| Action | `action_construction_contract_income` | `construction.contract` | 收入合同 |
| Action | `action_construction_contract_expense` | `construction.contract` | 支出合同 |
| Action | `action_construction_contract_line` | `construction.contract.line` | 合同行（无菜单，供关联/查找） |
| Model | `construction.contract` | `construction.contract` | 核心合同模型 |
| Model | `project.contract` | `project.contract` | 项目关联合同模型（财务需读，菜单不开放） |

### D5 Finance
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_finance_center` | `n/a` | 财务中心主入口 |
| Menu | `menu_payment_request` | `payment.request` | 付款/收款申请列表 |
| Action | `action_sc_finance_dashboard` | `payment.request` | 财务主动作（menu root action） |
| Action | `action_payment_request` | `payment.request` | 付款/收款申请 |
| Action | `action_sc_tier_review_my_payment_request` | `tier.review` | 待我审批（付款申请） |
| Server Action | `server_action_payment_request_on_approved` | `ir.actions.server` | 审批通过钩子 |
| Server Action | `server_action_payment_request_on_rejected` | `ir.actions.server` | 审批驳回钩子 |
| Model | `payment.request` | `payment.request` | 财务核心模型 |
| Model | `tier.review` | `tier.review` | 审批跟踪模型（需 reviewer 可读） |

### D6 Stock/Purchase
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_material_center` | `n/a` | 物资中心主入口 |
| Menu | `menu_project_material_plan` | `project.material.plan` | 物资计划 |
| Action | `action_project_material_plan` | `project.material.plan` | 物资计划列表 |
| Action | `action_material_plan_to_rfq_wizard` | `project.material.plan` | 计划转询价/采购向导 |
| Action | `action_sc_tier_review_my_material_plan` | `tier.review` | 待我审批（物资计划） |
| Server Action | `server_action_material_plan_tier_approved` | `ir.actions.server` | 物资计划审批通过 |
| Server Action | `server_action_material_plan_tier_rejected` | `ir.actions.server` | 物资计划审批驳回 |
| Model | `project.material.plan` | `project.material.plan` | 物资计划主模型 |
| Model | `purchase.order` | `purchase.order` | 采购单扩展了 project/wbs/cost_code（原生菜单） |
| Model | `stock.picking` | `stock.picking` | 出入库扩展项目维度（原生菜单） |

### D7 Workflow/Tier
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Menu | `menu_sc_workflow_root` | `n/a` | 工作流子树（配置中心下） |
| Action | `action_sc_workflow_def` | `sc.workflow.def` | 工作流定义 |
| Action | `action_sc_workflow_instance` | `sc.workflow.instance` | 实例列表 |
| Action | `action_sc_workflow_workitem` | `sc.workflow.workitem` | 工作项 |
| Action | `action_sc_workflow_log` | `sc.workflow.log` | 工作流日志 |
| Model | `sc.workflow.def` | `sc.workflow.def` | 工作流定义模型 |
| Model | `sc.workflow.instance` | `sc.workflow.instance` | 流程实例 |
| Model | `sc.workflow.workitem` | `sc.workflow.workitem` | 工作项 |
| Model | `sc.workflow.log` | `sc.workflow.log` | 工作流日志 |

### D8 Tools/Diagnostics
| Type | XML ID | Target Model | Notes |
|---|---|---|---|
| Action | `action_project_dashboard` | `project.project` | 项目驾驶舱（跨域统计） |
| Action | `action_project_cost_compare` | `project.cost.compare` | 预算 vs 实际报表 |
| Action | `action_project_profit_compare` | `project.profit.compare` | 经营利润报表 |
| Action | `action_project_cost_ledger` | `project.cost.ledger` | 成本台账（pivot/graph） |
| Action | `action_project_boq_import_wizard` | `project.boq.import.wizard` | BOQ 导入 |
| Action | `action_sc_project_document` | `sc.project.document` | 工程资料中心 |

## 5. 例外策略模式 (Exception Patterns)
| # | 模式 | 描述 | 案例 |
|---|---|---|---|
| 1 | 无菜单但需可读 | 出于数据选择或关联记录展示需要，某些模型无独立菜单，但需要对特定角色开放 `read` 权限。 | 财务角色（`finance_user`）需要读取 `project.contract` 用于关联付款申请，但不能看到“合同管理”菜单。 |
| 2 | 审批列表跨域读取 | `tier.review` action 只暴露“待我审批”，需要对关联单据授予只读，否则审批列表无法打开。 | `action_sc_tier_review_my_material_plan` / `action_sc_tier_review_my_payment_request` 需确保 reviewer 能读到对应 `project.material.plan` / `payment.request`。 |
| 3 | 仪表盘/报表跨域计算 | client/act_window 聚合字段会读取其他域的模型，需要确保 read/record rule 不被 compute 拦截。 | `action_project_dashboard` 计算指标读取 `project.cost.ledger` / 合同 / 预算；需在回归用例覆盖。 |
| 4 | 导入/批量向导 | 导入/批量操作不挂菜单，但需要显式 groups，且确认生成记录的 ACL/RR 不阻断。 | `action_project_boq_import_wizard`、`action_quota_import_wizard` 仅开放给能力组；导入后验证生成的 `project.boq.line`/`project.dictionary` 可被所属角色读取。 |

## 6. 风险清单与保底策略

**高风险动作的判定规则：** 满足以下任一条件的动作，必须拥有显式的 `groups_id` 定义。
1.  属于 Settings/Config（会改变系统行为）
2.  涉及 Master Data/财务账套（journals、tax、incoterms 等）
3.  属于 server action / automation / mass action（能批量影响数据）
4.  涉及导入/导出/删除/重建（不可逆或大范围影响）

### 高风险动作清单 (Top 20)

### 高风险动作清单（v0.3 全量候选）

| 类别 | XML ID | Type | Model | 风险原因 | 目标 capability group |
|---|---|---|---|---|---|
| Settings/Config | `base_setup.action_general_configuration` | act_window | `res.config.settings` | 修改全局配置 | `group_sc_super_admin` |
| Settings/Config | `account.action_account_config` | act_window | `res.config.settings` | 修改财务配置 | `group_sc_super_admin` |
| Settings/Config | `stock.action_stock_config_settings` | act_window | `res.config.settings` | 修改库存配置 | `group_sc_super_admin` |
| Settings/Config | `project.project_config_settings_action` | act_window | `res.config.settings` | 修改项目配置 | `group_sc_super_admin` |
| Settings/Config | `purchase.action_purchase_configuration` | act_window | `res.config.settings` | 修改采购配置 | `group_sc_super_admin` |
| Settings/Config | `action_project_cost_code` | act_window | `project.cost.code` | 成本科目主数据 | `group_sc_cap_config_admin` |
| Settings/Config | `action_sc_workflow_def` | act_window | `sc.workflow.def` | 工作流定义变更 | `group_sc_cap_config_admin` |
| Settings/Config | `digest.digest_digest_action` | act_window | `digest.digest` | 摘要邮件/调度配置 | `group_sc_super_admin` |
| Settings/Config | `digest.digest_tip_action` | act_window | `digest.digest` | 摘要提示配置 | `group_sc_super_admin` |
| Master Data | `account.action_account_journal_form` | act_window | `account.journal` | 会计科目主数据 | `group_sc_cap_finance_manager` |
| Master Data | `account.action_account_journal_group_list` | act_window | `account.journal.group` | 会计科目组 | `group_sc_cap_finance_manager` |
| Master Data | `account.action_incoterms_tree` | act_window | `account.incoterms` | 贸易术语主数据 | `group_sc_cap_finance_manager` |
| Import/Export/Mass | `base_import.action_import_data` | client_action | `base_import.import` | 任意模型导入（仅当 base_import 安装时有效；未安装则不加载） | `group_sc_super_admin` |
| Import/Export/Mass | `action_project_boq_import_wizard` | act_window | `project.boq.import.wizard` | BOQ 批量导入 | `group_sc_cap_cost_manager` |
| Import/Export/Mass | `action_project_task_from_boq_wizard` | act_window | `project.task.from.boq.wizard` | BOQ 转任务批量生成 | `group_sc_cap_cost_manager` |
| Import/Export/Mass | `action_quota_import_wizard` | act_window | `quota.import.wizard` | 定额库导入 | `group_sc_cap_config_admin` |
| Import/Export/Mass | `action_material_plan_to_rfq_wizard` | act_window | `project.material.plan` | 物资计划批量转询价/采购 | `group_sc_cap_material_user` / `manager` |
| Server Action / Automation | `base.action_module_upgrade` | server_action | `ir.actions.server` | 模块升级（如本环境未定义该 xmlid，则无需补丁） | `group_sc_super_admin` |
| Server Action / Automation | `server_action_material_plan_tier_approved` | server_action | `project.material.plan` | 审批回调自动写入 | `group_sc_cap_material_manager` |
| Server Action / Automation | `server_action_material_plan_tier_rejected` | server_action | `project.material.plan` | 审批回调驳回 | `group_sc_cap_material_manager` |
| Server Action / Automation | `server_action_payment_request_on_approved` | server_action | `payment.request` | 审批通过后动作 | `group_sc_cap_finance_manager` |
| Server Action / Automation | `server_action_payment_request_on_rejected` | server_action | `payment.request` | 审批驳回后动作 | `group_sc_cap_finance_manager` |
| Server Action / Automation | `stock.action_replenishment` | server_action | `stock.warehouse.orderpoint` | 库存补货批量生成 | `group_sc_cap_material_manager`（理想映射；当前原生为 `stock.group_stock_user`，需桥接） |
| 导入/删除（非 Odoo Action） | `db_reset` (Makefile) | shell | `n/a` | 数据库重置 | 运维动作，需人工确认 |

<!-- PERM_MATRIX_START -->
```json
{
  "super_admin": {
    "groups": ["smart_construction_core.group_sc_super_admin"],
    "menus_allow": [
      "smart_construction_core.menu_sc_root",
      "smart_construction_core.menu_sc_project_center",
      "smart_construction_core.menu_sc_finance_center",
      "smart_construction_core.menu_sc_contract_center"
    ],
    "menus_deny": [],
    "actions_allow": [
      "smart_construction_core.action_project_dashboard",
      "smart_construction_core.action_payment_request",
      "smart_construction_core.action_construction_contract",
      "smart_construction_core.action_sc_workflow_def"
    ],
    "actions_deny": []
  },
  "project_read": {
    "groups": ["smart_construction_core.group_sc_cap_project_read"],
    "menus_allow": ["smart_construction_core.menu_sc_project_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_project_dashboard"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "project_manager": {
    "groups": ["smart_construction_core.group_sc_cap_project_manager"],
    "menus_allow": ["smart_construction_core.menu_sc_project_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_project_wbs"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "finance_read": {
    "groups": ["smart_construction_core.group_sc_cap_finance_read"],
    "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
    "menus_deny": ["smart_construction_core.menu_sc_project_center"],
    "actions_allow": ["smart_construction_core.action_payment_request"],
    "actions_deny": ["smart_construction_core.action_project_wbs"]
  },
  "finance_user": {
    "groups": ["smart_construction_core.group_sc_cap_finance_user"],
    "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
    "menus_deny": ["smart_construction_core.menu_sc_project_center"],
    "actions_allow": ["smart_construction_core.action_payment_request"],
    "actions_deny": ["smart_construction_core.action_project_material_plan"]
  },
  "finance_manager": {
    "groups": ["smart_construction_core.group_sc_cap_finance_manager"],
    "menus_allow": ["smart_construction_core.menu_sc_finance_center"],
    "menus_deny": ["smart_construction_core.menu_sc_project_center"],
    "actions_allow": ["smart_construction_core.action_sc_tier_review_my_payment_request"],
    "actions_deny": ["smart_construction_core.action_project_material_plan"]
  },
  "contract_user": {
    "groups": ["smart_construction_core.group_sc_cap_contract_user"],
    "menus_allow": ["smart_construction_core.menu_sc_contract_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_construction_contract"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "contract_manager": {
    "groups": ["smart_construction_core.group_sc_cap_contract_manager"],
    "menus_allow": ["smart_construction_core.menu_sc_contract_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_construction_contract"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "cost_manager": {
    "groups": ["smart_construction_core.group_sc_cap_cost_manager"],
    "menus_allow": ["smart_construction_core.menu_sc_project_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_project_cost_compare"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "material_manager": {
    "groups": ["smart_construction_core.group_sc_cap_material_manager"],
    "menus_allow": ["smart_construction_core.menu_sc_material_center"],
    "menus_deny": ["smart_construction_core.menu_sc_finance_center"],
    "actions_allow": ["smart_construction_core.action_project_material_plan"],
    "actions_deny": ["smart_construction_core.action_payment_request"]
  },
  "config_admin": {
    "groups": ["smart_construction_core.group_sc_cap_config_admin"],
    "menus_allow": ["smart_construction_core.menu_sc_root"],
    "menus_deny": [],
    "actions_allow": ["smart_construction_core.action_sc_workflow_def"],
    "actions_deny": []
  }
}
```
<!-- PERM_MATRIX_END -->

> 说明：上述列表以 “Settings/Config 全量 + Import/Export/Mass 全量 + Server Action/Automation 全量” 为口径。若新增向导/自动化，请按同一标准补充表项并绑定 SC 能力组（不要直接绑原生组）。

### Compute / Related 风险点清单（纳入回归用例）
- `action_project_dashboard`：跨域读取项目、合同、预算、成本台账，需验证 project/contract/ledger 的读权限 + 记录规则不会在 compute 中报 AccessError。
- `action_project_cost_compare` / `action_project_profit_compare`：pivot 汇总依赖 `project.cost.ledger` 与合同/预算视图，需验证成本/合同读权限。
- `action_project_cost_ledger`：graph/pivot 读取多域字段（partner/cost_code/project），需验证成本读权限与记录规则。
- `action_sc_tier_review_my_material_plan` / `action_sc_tier_review_my_payment_request`：审批列表读 `tier.review` + 关联单据（物资计划/付款申请），需确保 reviewer 有 read 权限，否则列表打不开。

### CI 测试分层（v0.3 建议）
- `sc_smoke`（默认）：最小烟囱 + 基础数据验证（现有 smoke_* 用例）。
- `sc_gate`（默认）：权限/门禁守卫（action_groups_gate + 角色矩阵回归）。
- `sc_regression`（按需）：域级最小回归（项目/合同/物资/财务/成控跨域计算与权限）。已给预算/合同/成本对比/利润对比/库存成本等测试添加 `sc_regression` 标签。
> Makefile 默认 `TEST_TAGS=sc_smoke,sc_gate`；如需回归层，执行 `make test-ci TEST_TAGS=sc_smoke,sc_gate,sc_regression`。

### 当前 CI 报警/错误跟踪
- 警告：多个测试未标注 `@tagged(..., at_install/post_install)`，为标准 Odoo 警示，但不影响执行。
- 最新错误集中在 `test_profit_compare`（销售日记账字段不支持 default_debit_account_id）和 `test_stock_cost`（台账未生成或过滤为空）已在用例中调整。

## 7. 变更记录
- v0.3: 建立全域清单和例外策略模式，升级为可审计的 v0.3 版本。
- v0.2: 文档骨架建立，并完成 D5 Finance 域的权限梳理示范。

---

### v0.3 Done 条件
- [ ] v0.3 权限矩阵：D1-D8 全覆盖（每域至少 1 个入口 + 1 个动作 + 1 个模型策略）
- [ ] 高风险动作清单：Settings/Import/ServerAction 三类 **全量**列出（不是抽样）
- [ ] action groups：高风险动作 **100% groups_id** 覆盖
- [ ] CI：新增“角色最小回归集”，能定位到角色/域/动作粒度
