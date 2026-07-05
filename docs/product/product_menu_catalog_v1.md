# 产品菜单台账 V1

本台账由运行时 Odoo 菜单事实生成，只读取 `ir.ui.menu`、动作、权限组和 XMLID，不从用户确认历史数据反推产品菜单。

## 运行时来源

- database: `sc_demo`
- generated_at: `2026-07-05T02:44:57.873144+00:00`
- roots: `smart_construction_core.menu_sc_root, smart_core.menu_smart_core_platform_root`
- visible_login_probe: `admin, wutao, demo_business_full, demo_role_finance, demo_role_executive`

## 总览

- menu_count: `518`
- active_menu_count: `440`
- inactive_menu_count: `78`
- action_menu_count: `428`
- needs_review_count: `0`
- internal_history_business_visible_count: `0`
- ordinary_business_system_config_visible_count: `0`
- business_config_legacy_count: `0`
- business_config_legacy_active_count: `0`
- runtime_user_menu_without_xmlid_count: `0`
- formal_center_inactive_history_count: `0`

## 分层定义

- `formal_product`: 正式产品办理入口，用于日常施工业务的新增、编辑、查询、分析和继续办理。
- `system_config`: 系统/产品配置入口，包括低代码恢复入口、字典、规则、定额、审批和管理配置。
- `user_config`: 租户或用户自主管理的偏好、个性化和运行时配置入口。
- `history_acceptance`: 历史数据承载、用户核对、旧系统事实、迁移连续性和验收过渡入口。
- `dev_governance`: 平台内核、场景治理、发布运维、诊断和开发治理入口。

## 分层统计

| Layer | Count |
| --- | ---: |
| `formal_product` | 266 |
| `system_config` | 31 |
| `user_config` | 0 |
| `history_acceptance` | 191 |
| `dev_governance` | 30 |

## 正式产品入口概览

| 入口 | XMLID | 可见性探针用户 |
| --- | --- | --- |
| 智慧施工管理平台 / 人事行政 | `smart_construction_core.menu_sc_hr_admin_center` | admin, wutao, demo_business_full, demo_role_finance |
| 智慧施工管理平台 / 合同中心 | `smart_construction_core.menu_sc_contract_center` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |
| 智慧施工管理平台 / 基础资料 | `smart_construction_core.menu_sc_master_data_center` | admin, wutao, demo_business_full |
| 智慧施工管理平台 / 成本中心 | `smart_construction_core.menu_sc_cost_center` | admin, wutao, demo_business_full |
| 智慧施工管理平台 / 施工管理 | `smart_construction_core.menu_sc_construction_management_center` | admin, wutao, demo_business_full, demo_role_executive |
| 智慧施工管理平台 / 智慧大屏 | `smart_construction_core.menu_sc_projection_root` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |
| 智慧施工管理平台 / 物资与分包 | `smart_construction_core.menu_sc_material_center` | admin, wutao, demo_business_full |
| 智慧施工管理平台 / 税务中心 | `smart_construction_core.menu_sc_tax_center` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |
| 智慧施工管理平台 / 统计分析 | `smart_construction_core.menu_sc_data_center` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |
| 智慧施工管理平台 / 财务中心 | `smart_construction_core.menu_sc_finance_center` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |
| 智慧施工管理平台 / 资料证照 | `smart_construction_core.menu_sc_document_admin_center` | admin, wutao, demo_business_full, demo_role_finance |
| 智慧施工管理平台 / 项目中心 | `smart_construction_core.menu_sc_project_center` | admin, wutao, demo_business_full, demo_role_executive |
| 智慧施工管理平台 / 首页 | `smart_construction_core.menu_sc_workspace_center` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive |

## 顶层菜单

| Menu | Layer | Visible Probe Logins | XMLID |
| --- | --- | --- | --- |
| 平台内核 | `dev_governance` | admin | `smart_core.menu_smart_core_platform_root` |
| 平台内核 / 产品发布 | `dev_governance` | admin | `smart_core.menu_smart_core_release_root` |
| 平台内核 / 公司访问 | `dev_governance` | admin | `smart_core.menu_smart_core_company_access_root` |
| 智慧施工管理平台 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_root` |
| 智慧施工管理平台 / 业务配置 | `system_config` | admin, wutao | `smart_construction_core.menu_sc_business_config_center` |
| 智慧施工管理平台 / 人事行政 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance | `smart_construction_core.menu_sc_hr_admin_center` |
| 智慧施工管理平台 / 合同中心 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_contract_center` |
| 智慧施工管理平台 / 基础资料 | `formal_product` | admin, wutao, demo_business_full | `smart_construction_core.menu_sc_master_data_center` |
| 智慧施工管理平台 / 成本中心 | `formal_product` | admin, wutao, demo_business_full | `smart_construction_core.menu_sc_cost_center` |
| 智慧施工管理平台 / 施工管理 | `formal_product` | admin, wutao, demo_business_full, demo_role_executive | `smart_construction_core.menu_sc_construction_management_center` |
| 智慧施工管理平台 / 智慧大屏 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_projection_root` |
| 智慧施工管理平台 / 物资与分包 | `formal_product` | admin, wutao, demo_business_full | `smart_construction_core.menu_sc_material_center` |
| 智慧施工管理平台 / 用户核对菜单 | `history_acceptance` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_scbs55_user_acceptance_root` |
| 智慧施工管理平台 / 用户验收 | `history_acceptance` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_user_acceptance_root` |
| 智慧施工管理平台 / 税务中心 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_tax_center` |
| 智慧施工管理平台 / 系统配置 | `system_config` | admin | `smart_construction_core.menu_sc_config_center` |
| 智慧施工管理平台 / 统计分析 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_data_center` |
| 智慧施工管理平台 / 财务中心 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_finance_center` |
| 智慧施工管理平台 / 资料证照 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance | `smart_construction_core.menu_sc_document_admin_center` |
| 智慧施工管理平台 / 项目中心 | `formal_product` | admin, wutao, demo_business_full, demo_role_executive | `smart_construction_core.menu_sc_project_center` |
| 智慧施工管理平台 / 首页 | `formal_product` | admin, wutao, demo_business_full, demo_role_finance, demo_role_executive | `smart_construction_core.menu_sc_workspace_center` |

## 产品菜单树

- 平台内核 [`dev_governance`]
  - 产品发布 [`dev_governance`]
    - 产品策略 [`dev_governance`] -> `sc.product.policy`
    - 发布动作 [`dev_governance`] -> `sc.release.action`
    - 发布快照 [`dev_governance`] -> `sc.edition.release.snapshot`
    - 场景快照 [`dev_governance`] -> `sc.scene.snapshot`
  - 公司访问 [`dev_governance`]
    - 授权快照 [`dev_governance`] -> `sc.entitlement`
    - 用量统计 [`dev_governance`] -> `sc.usage.counter`
    - 统一登录路由 [`dev_governance`] -> `sc.login.route`
    - 订阅套餐 [`dev_governance`] -> `sc.subscription.plan`
    - 订阅实例 [`dev_governance`] -> `sc.subscription`
    - 运营任务 [`dev_governance`] -> `sc.ops.job`
- 智慧施工管理平台 [`formal_product`]
  - 业务配置 [`system_config`]
    - 业务分类字典 [`system_config`] -> `sc.business.category`
    - 业务配置工作台 [`system_config`] -> `ui.business.config.contract`
    - 定额字典 [`system_config`]
      - 专业 [`system_config`] -> `project.dictionary`
      - 全部定额字典 [`system_config`] -> `project.dictionary`
      - 四川定额导入 [`system_config`] -> `quota.import.wizard`
      - 子目 [`system_config`] -> `project.dictionary`
      - 定额项目 [`system_config`] -> `project.dictionary`
      - 章节 [`system_config`] -> `project.dictionary`
    - 定额库 [`system_config`]
      - 定额中心（左树右明细） [`system_config`] -> `project.dictionary`
      - 定额子目 [`system_config`] -> `project.dictionary`
      - 定额层级 [`system_config`] -> `project.dictionary`
    - 审批岗位人员 [`system_config`] -> `sc.approval.scope`
    - 审批配置 [`system_config`] -> `sc.approval.policy`
    - 数据字典 [`system_config`] -> `sc.dictionary`
    - 新增表单字段 [`system_config`] -> `ui.form.custom.field.wizard`
    - 菜单配置 [`system_config`] -> `ui.menu.config.policy`
    - 表单字段配置 [`system_config`] -> `ui.form.field.policy`
    - 阶段要求配置 [`system_config`] -> `sc.project.stage.requirement.item`
    - 预算类型 [`system_config`] -> `project.cost.code`
  - 人事行政 [`formal_product`]
    - 印章使用审批表 [`formal_product`] -> `sc.office.admin.document`
    - 奖金 [`formal_product`] -> `sc.hr.payroll.document`
    - 工资登记 [`formal_product`] -> `sc.hr.payroll.document`
    - 社保人员登记 [`formal_product`] -> `sc.hr.payroll.document`
    - 社保登记 [`formal_product`] -> `sc.hr.payroll.document`
    - 补助 [`formal_product`] -> `sc.hr.payroll.document`
    - 请假/休假审批单 [`formal_product`] -> `sc.office.admin.document`
    - 项目管理人员工资登记 [`formal_product` inactive] -> `sc.hr.payroll.document`
  - 合同中心 [`formal_product`] -> `construction.contract`
    - 合同办理 [`formal_product`] -> `construction.contract`
    - 合同办理 [`formal_product` inactive] -> `construction.contract`
    - 待我审批（一般合同（公司）） [`formal_product` inactive] -> `sc.general.contract`
    - 待我审批（项目合同） [`formal_product` inactive] -> `construction.contract`
    - 支出合同台账 [`formal_product`] -> `sc.expense.contract.ledger`
      - 一般合同（公司） [`formal_product`] -> `sc.general.contract`
      - 其他合同 [`formal_product`] -> `construction.contract.expense`
      - 分包合同 [`formal_product`] -> `construction.contract.expense`
      - 劳务合同 [`formal_product`] -> `construction.contract.expense`
      - 支出合同台账 [`formal_product`] -> `sc.expense.contract.ledger`
      - 支出合同执行 [`formal_product`] -> `construction.contract.expense`
      - 支出合同签证 [`formal_product`] -> `sc.settlement.adjustment`
      - 支出合同结算 [`formal_product`] -> `sc.settlement.order`
      - 材料合同 [`formal_product`] -> `construction.contract.expense`
      - 正常合同 [`formal_product`] -> `construction.contract.expense`
      - 租赁合同 [`formal_product`] -> `construction.contract.expense`
      - 补充合同 [`formal_product`] -> `construction.contract.expense`
    - 收入合同台账 [`formal_product`] -> `sc.income.contract.ledger`
      - 合同履约事件 [`formal_product`] -> `sc.contract.event`
      - 收入合同台账 [`formal_product`] -> `sc.income.contract.ledger`
      - 收入合同执行 [`formal_product`] -> `construction.contract.income`
      - 收入合同签证 [`formal_product`] -> `sc.settlement.adjustment`
      - 收入合同结算 [`formal_product`] -> `sc.settlement.order`
      - 施工合同 [`formal_product`] -> `construction.contract.income`
      - 项目收入合同 [`formal_product`] -> `construction.contract.income`
  - 基础资料 [`formal_product`]
    - 供应商 [`formal_product`] -> `res.partner`
    - 客户 [`formal_product`] -> `res.partner`
    - 组织架构 [`formal_product`] -> `hr.department`
  - 成本中心 [`formal_product`]
    - WBS/分部分项 [`formal_product`] -> `construction.work.breakdown`
    - 成本台账 [`formal_product`] -> `project.cost.ledger`
    - 成本汇总 [`formal_product`] -> `project.cost.compare`
    - 目标成本 [`formal_product`] -> `project.budget`
    - 经营利润 [`formal_product`] -> `project.profit.compare`
    - 进度计量 [`formal_product`] -> `project.progress.entry`
    - 预算清单分摊 [`formal_product`] -> `project.budget.cost.alloc`
  - 施工管理 [`formal_product`]
    - 安全复验 [`formal_product`] -> `sc.safety.recheck`
    - 安全整改 [`formal_product`] -> `sc.safety.rectification`
    - 安全检查 [`formal_product`] -> `sc.safety.issue`
    - 施工日志 [`formal_product`] -> `sc.construction.diary`
    - 计划汇报 [`formal_product`] -> `sc.plan.report`
    - 计划管理 [`formal_product`] -> `sc.plan`
    - 质量复验 [`formal_product`] -> `sc.quality.recheck`
    - 质量整改 [`formal_product`] -> `sc.quality.rectification`
    - 质量检查 [`formal_product`] -> `sc.quality.issue`
    - 进度管理 [`formal_product`] -> `project.progress.entry`
  - 智慧大屏 [`formal_product`]
    - 公司驾驶舱 [`formal_product`] -> `sc.operating.metrics.project`
    - 成本大屏 [`formal_product`] -> `sc.dashboard.cockpit.fact`
    - 成本驾驶舱 [`formal_product`] -> `sc.dashboard.cockpit.fact`
    - 经营大屏 [`formal_product`] -> `sc.operating.metrics.project`
    - 经营指标 [`formal_product` inactive]
    - 资金驾驶舱 [`formal_product`] -> `sc.dashboard.cockpit.fact`
    - 项目驾驶舱 [`formal_product`] -> `project.project`
  - 物资与分包 [`formal_product`]
    - 专业分包 [`formal_product`]
      - 分包方单 [`formal_product`] -> `sc.subcontract.request`
      - 分包申请 [`formal_product`] -> `sc.subcontract.request`
      - 分包登记 [`formal_product`] -> `sc.subcontract.register`
      - 分包结算 [`formal_product`] -> `sc.subcontract.settlement`
      - 分包计划 [`formal_product`] -> `sc.subcontract.plan`
    - 劳务管理 [`formal_product`]
      - 劳务申请 [`formal_product`] -> `sc.labor.request`
      - 劳务结算 [`formal_product`] -> `sc.labor.settlement`
      - 劳务计划 [`formal_product`] -> `sc.labor.plan`
      - 方单 [`formal_product`] -> `sc.labor.usage`
      - 考勤记录 [`formal_product`] -> `sc.attendance.checkin`
      - 零星用工 [`formal_product`] -> `sc.labor.usage`
    - 周转材料租赁 [`formal_product`]
      - 租入 [`formal_product`] -> `sc.material.rental.order`
      - 租赁单 [`formal_product`] -> `sc.material.rental.order`
      - 租赁结算 [`formal_product`] -> `sc.material.rental.settlement`
      - 租赁计划 [`formal_product`] -> `sc.material.rental.plan`
      - 还租 [`formal_product`] -> `sc.material.rental.order`
    - 待我审批（物资计划） [`formal_product` inactive] -> `tier.review`
    - 机械设备 [`formal_product`]
      - 机械台班记录 [`formal_product`] -> `sc.equipment.usage`
      - 设备使用登记 [`formal_product`] -> `sc.equipment.usage`
      - 设备申请 [`formal_product`] -> `sc.equipment.request`
      - 设备结算 [`formal_product`] -> `sc.equipment.settlement`
      - 设备计划 [`formal_product`] -> `sc.equipment.plan`
    - 材料管理 [`formal_product`]
      - 入库单 [`formal_product`] -> `sc.material.inbound`
      - 出库单 [`formal_product`] -> `sc.material.outbound`
      - 报价单 [`formal_product`] -> `sc.material.rfq`
      - 材料价格库 [`formal_product`] -> `sc.material.price`
      - 材料损耗 [`formal_product`] -> `sc.material.outbound`
      - 材料档案 [`formal_product`] -> `sc.material.catalog`
      - 材料结算 [`formal_product`] -> `sc.material.settlement`
      - 材料计划 [`formal_product`] -> `project.material.plan`
      - 材料调拨 [`formal_product`] -> `sc.material.outbound`
      - 材料进场验收 [`formal_product`] -> `sc.material.acceptance`
      - 询比价 [`formal_product`] -> `sc.material.rfq`
      - 退库办理 [`formal_product`] -> `sc.material.outbound`
      - 采购申请 [`formal_product`] -> `sc.material.purchase.request`
      - 采购订单 [`formal_product`] -> `purchase.order`
  - 用户核对菜单 [`history_acceptance`]
    - 人事行政 [`history_acceptance`]
      - 印章使用审批表 [`history_acceptance`] -> `sc.office.admin.document`
      - 奖金 [`history_acceptance`] -> `sc.hr.payroll.document`
      - 工资登记 [`history_acceptance`] -> `sc.hr.payroll.document`
      - 社保人员登记 [`history_acceptance`] -> `sc.hr.payroll.document`
      - 社保登记 [`history_acceptance`] -> `sc.hr.payroll.document`
      - 补助 [`history_acceptance`] -> `sc.hr.payroll.document`
      - 请假/休假审批单 [`history_acceptance`] -> `sc.office.admin.document`
    - 付款 [`history_acceptance`]
      - 往来单位付款 [`history_acceptance`] -> `sc.payment.execution`
      - 支付申请 [`history_acceptance`] -> `payment.request`
    - 分析大屏 [`history_acceptance`]
      - 成本大屏 [`history_acceptance`] -> `sc.dashboard.cockpit.fact`
      - 经营大屏 [`history_acceptance`] -> `sc.operating.metrics.project`
    - 办公资料 [`history_acceptance`]
      - 公司资料存档 [`history_acceptance`] -> `sc.document.admin.document`
    - 发票税务 [`history_acceptance`]
      - 外经证登记 [`history_acceptance`] -> `sc.legacy.payment.residual.fact`
      - 开票申请 [`history_acceptance`] -> `sc.invoice.registration`
      - 开票登记 [`history_acceptance`] -> `sc.invoice.registration`
      - 抵扣登记 [`history_acceptance`] -> `sc.tax.deduction.registration`
      - 进项上报 [`history_acceptance`] -> `sc.legacy.invoice.tax.fact`
      - 预缴税款 [`history_acceptance`] -> `sc.invoice.registration`
    - 合同 [`history_acceptance`]
      - 施工合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
    - 基础资料 [`history_acceptance`]
      - 供应商/合作单位 [`history_acceptance`] -> `sc.business.entity`
      - 往来单位 [`history_acceptance`] -> `sc.business.entity`
    - 成本报表 [`history_acceptance`]
      - 供货合同分析 [`history_acceptance`] -> `sc.legacy.supplier.contract.pricing.fact`
      - 发票分析报表 [`history_acceptance`] -> `sc.invoice.analysis.summary`
      - 发票成本进度报表 [`history_acceptance`] -> `sc.invoice.cost.progress.summary`
      - 库存统计表（新） [`history_acceptance`] -> `sc.material.stock.summary`
      - 成本统计表（综合） [`history_acceptance`] -> `sc.comprehensive.cost.summary`
      - 投标保证金报表 [`history_acceptance`] -> `sc.tender.guarantee.summary`
      - 账户收支统计表 [`history_acceptance`] -> `sc.account.income.expense.summary`
    - 扣款 [`history_acceptance`]
      - 扣款单 [`history_acceptance`] -> `sc.tax.deduction.registration`
      - 扣款实缴登记 [`history_acceptance`] -> `sc.expense.claim`
      - 扣款实缴退回 [`history_acceptance`] -> `sc.expense.claim`
    - 投标 [`history_acceptance`]
      - 投标报名管理 [`history_acceptance`] -> `tender.bid`
      - 投标报名费申请 [`history_acceptance`] -> `tender.doc.purchase`
    - 收支 [`history_acceptance`]
      - 公司财务支出 [`history_acceptance`] -> `sc.expense.claim`
      - 收入 [`history_acceptance`] -> `sc.receipt.income`
    - 收款 [`history_acceptance`]
      - 到款确认表 [`history_acceptance`] -> `sc.legacy.fund.confirmation.document`
    - 组织人员 [`history_acceptance`]
      - 公司人员名册（配置） [`history_acceptance`] -> `sc.legacy.user.profile`
      - 组织机构 [`history_acceptance`] -> `hr.department`
    - 证照资料 [`history_acceptance`]
      - 借阅申请 [`history_acceptance`] -> `sc.document.admin.document`
      - 证照登记 [`history_acceptance`] -> `sc.document.admin.document`
    - 财税报表 [`history_acceptance`]
      - 应收应付报表 [`history_acceptance`] -> `sc.ar.ap.report.summary`
      - 项目经营统计表 [`history_acceptance`] -> `sc.project.operation.summary`
    - 费用报销 [`history_acceptance`]
      - 报销申请 [`history_acceptance`] -> `sc.expense.claim`
    - 资金保证金 [`history_acceptance`]
      - 付款还保证金 [`history_acceptance`] -> `tender.guarantee`
      - 付款还保证金退回 [`history_acceptance`] -> `tender.guarantee`
      - 自筹保证金 [`history_acceptance` inactive] -> `tender.guarantee`
      - 自筹保证金退回 [`history_acceptance` inactive] -> `tender.guarantee`
    - 资金借还 [`history_acceptance`]
      - 借款申请 [`history_acceptance`] -> `sc.financing.loan`
      - 还款登记 [`history_acceptance`] -> `sc.financing.loan`
    - 资金日报 [`history_acceptance`]
      - 资金日报表 [`history_acceptance`] -> `sc.legacy.fund.daily.line`
    - 资金账户 [`history_acceptance`]
      - 账户间资金往来 [`history_acceptance`] -> `sc.fund.account.operation`
    - 项目台账（公司/项目/经营方式） [`history_acceptance`] -> `project.project`
    - 项目资金 [`history_acceptance`]
      - 承包人借项目款 [`history_acceptance`] -> `sc.financing.loan`
      - 承包人还项目款 [`history_acceptance`] -> `sc.expense.claim`
      - 项目借公司款登记 [`history_acceptance`] -> `sc.financing.loan`
      - 项目还公司款登记 [`history_acceptance`] -> `sc.financing.loan`
  - 用户验收 [`history_acceptance`]
    - 直营项目系统菜单 [`history_acceptance`]
      - 分包管理类单据 [`history_acceptance`]
        - 分包方单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 分包结算单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 劳务管理类单据 [`history_acceptance`]
        - 劳务结算 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 方单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 零星用工 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 合同类单据 [`history_acceptance`]
        - 供货合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 供货合同（数据） [`history_acceptance`] -> `sc.legacy.supplier.contract.pricing.fact`
        - 分包合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 劳务合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 施工合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 机械合同（合同） [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 租赁合同 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 机械与租赁管理类单据 [`history_acceptance`]
        - 机械台班记录 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 机械结算单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 租入 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 租赁结算单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 还租 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 材料管理类单据 [`history_acceptance`]
        - 入库 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 库存统计表（新） [`history_acceptance`] -> `sc.material.stock.summary`
        - 报价单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 材料结算单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 材料计划 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 费用与资金管理类单据 [`history_acceptance`]
        - 充值登记 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 加油登记 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 工程结算单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 工程进度收款 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 往来单位付款 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 总包进项上报 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 成本统计表（数据） [`history_acceptance`] -> `sc.comprehensive.cost.summary`
        - 支付申请 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 油卡登记 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 管理人员工资表 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 进项上报 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
        - 项目费用报销单 [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
      - 项目管理类单据 [`history_acceptance`]
        - 施工日志（新） [`history_acceptance`] -> `sc.legacy.direct.acceptance.fact`
  - 税务中心 [`formal_product`]
    - 发票税务 [`formal_product`]
      - 外经证登记 [`history_acceptance`] -> `sc.legacy.payment.residual.fact`
      - 抵扣登记 [`formal_product`] -> `sc.tax.deduction.registration`
      - 进项税额上报 [`formal_product`] -> `sc.invoice.registration`
      - 销项开票申请 [`formal_product`] -> `sc.invoice.registration`
      - 销项开票登记 [`formal_product`] -> `sc.invoice.registration`
      - 预缴税款 [`formal_product`] -> `sc.invoice.registration`
    - 财税报表 [`formal_product`]
      - 公司经营情况表 [`formal_product`] -> `sc.company.operation.summary`
      - 应收应付报表 [`formal_product` inactive] -> `sc.ar.ap.company.summary`
      - 项目经营统计表 [`formal_product`] -> `sc.operating.metrics.project`
  - 系统配置 [`system_config`]
    - 历史物料档案（内部） [`history_acceptance` inactive] -> `sc.legacy.material.detail`
    - 历史财务事实（内部） [`system_config`]
      - 历史供应商合同计价方式 [`history_acceptance`] -> `sc.legacy.supplier.contract.pricing.fact`
      - 历史发票登记 [`history_acceptance`] -> `sc.legacy.invoice.registration.line`
      - 历史发票税额 [`history_acceptance`] -> `sc.legacy.invoice.tax.fact`
      - 历史发票附加税 [`history_acceptance`] -> `sc.legacy.invoice.surcharge.fact`
      - 历史扣款调整 [`history_acceptance`] -> `sc.legacy.deduction.adjustment.line`
      - 历史抵扣税额 [`history_acceptance`] -> `sc.legacy.tax.deduction.fact`
      - 历史收款收入 [`history_acceptance`] -> `sc.legacy.receipt.income.fact`
      - 历史文件索引 [`history_acceptance`] -> `sc.legacy.file.index`
      - 历史流程扩展事实 [`history_acceptance`] -> `sc.legacy.workflow.detail.fact`
      - 历史自筹资金 [`history_acceptance`] -> `sc.legacy.self.funding.fact`
      - 历史融资借款 [`history_acceptance`] -> `sc.legacy.financing.loan.fact`
      - 历史财税辅助事实 [`history_acceptance`] -> `sc.legacy.finance.auxiliary.fact`
      - 历史费用/保证金 [`history_acceptance`] -> `sc.legacy.expense.deposit.fact`
      - 历史费用报销明细 [`history_acceptance`] -> `sc.legacy.expense.reimbursement.line`
      - 历史资金日报 [`history_acceptance`] -> `sc.legacy.fund.daily.snapshot.fact`
      - 历史资金日报明细 [`history_acceptance`] -> `sc.legacy.fund.daily.line`
      - 历史资金确认 [`history_acceptance`] -> `sc.legacy.fund.confirmation.line`
      - 历史项目资金余额 [`history_acceptance`] -> `sc.legacy.project.fund.balance.fact`
      - 流程工作台 [`system_config`] -> `sc.history.todo`
    - 历史验收归档（内部） [`system_config` inactive]
      - SCBS旧库事实暂存 [`history_acceptance` inactive] -> `sc.legacy.scbs.fact.staging`
      - SCBS旧库材料映射 [`history_acceptance` inactive] -> `sc.legacy.scbs.material.map`
      - 供应商合同计价事实 [`history_acceptance` inactive] -> `sc.legacy.supplier.contract.pricing.fact`
      - 供货合同 [`history_acceptance` inactive] -> `sc.legacy.supplier.contract.pricing.fact`
      - 供货合同 [`history_acceptance` inactive] -> `sc.legacy.supplier.contract.pricing.fact`
      - 供货合同 [`history_acceptance` inactive] -> `sc.legacy.supplier.contract.pricing.fact`
      - 充值登记 [`history_acceptance` inactive] -> `sc.legacy.fuel.card.recharge.fact`
      - 公司人员名册 [`history_acceptance` inactive] -> `sc.legacy.user.profile`
      - 到款确认表 [`history_acceptance` inactive] -> `sc.legacy.fund.confirmation.document`
      - 加油登记 [`history_acceptance` inactive] -> `sc.legacy.fuel.card.refuel.fact`
      - 劳务结算候选核对 [`system_config` inactive] -> `sc.labor.settlement.candidate`
      - 历史业务事实原貌承接 [`history_acceptance` inactive] -> `sc.legacy.business.fact.residual`
      - 历史付款残余事实 [`history_acceptance` inactive] -> `sc.legacy.payment.residual.fact`
      - 历史付款退款/调整 [`history_acceptance` inactive] -> `sc.legacy.payment.adjustment.fact`
      - 历史企业级数据核对 [`history_acceptance` inactive] -> `sc.legacy.enterprise.business.fact`
      - 历史劳务/分包事实 [`history_acceptance` inactive] -> `sc.legacy.labor.subcontract.fact`
      - 历史劳务/分包事实 [`history_acceptance` inactive] -> `sc.legacy.labor.subcontract.fact`
      - 历史投标报名 [`history_acceptance` inactive] -> `sc.legacy.tender.registration.fact`
      - 历史收入票据事实 [`history_acceptance` inactive] -> `sc.legacy.income.invoice.fact`
      - 历史物资库存事实 [`history_acceptance` inactive] -> `sc.legacy.material.stock.fact`
      - 历史设备/租赁事实 [`history_acceptance` inactive] -> `sc.legacy.equipment.lease.fact`
      - 历史设备/租赁事实 [`history_acceptance` inactive] -> `sc.legacy.equipment.lease.fact`
      - 历史费用/保证金流入退回 [`history_acceptance` inactive] -> `sc.legacy.expense.deposit.fact`
      - 历史费用/保证金流出 [`history_acceptance` inactive] -> `sc.legacy.expense.deposit.fact`
      - 历史费用报销明细 [`history_acceptance` inactive] -> `sc.legacy.expense.reimbursement.line`
      - 历史资金日报明细 [`history_acceptance` inactive] -> `sc.legacy.fund.daily.line`
      - 历史采购/一般合同事实 [`history_acceptance` inactive] -> `sc.legacy.purchase.contract.fact`
      - 历史采购/一般合同事实 [`history_acceptance` inactive] -> `sc.legacy.purchase.contract.fact`
      - 工程进度收款 [`history_acceptance` inactive] -> `sc.legacy.engineering.progress.receipt`
      - 工程进度收款 [`history_acceptance` inactive] -> `sc.legacy.engineering.progress.receipt`
      - 工程进度收款（直营） [`history_acceptance` inactive] -> `sc.legacy.engineering.progress.receipt`
      - 待我审批（历史采购/一般合同事实） [`history_acceptance` inactive] -> `sc.legacy.purchase.contract.fact`
      - 成本发票明细表 [`history_acceptance` inactive] -> `sc.legacy.invoice.registration.line`
      - 扣款/结算调整 [`history_acceptance` inactive] -> `sc.legacy.deduction.adjustment.line`
      - 扣款税费核对 [`system_config` inactive]
      - 投标保证金报表 [`history_acceptance` inactive] -> `sc.legacy.expense.deposit.fact`
      - 抵扣税额 [`history_acceptance` inactive] -> `sc.legacy.tax.deduction.fact`
      - 旧库业务主体映射 [`history_acceptance` inactive] -> `sc.legacy.business.entity.map`
      - 旧库往来单位映射 [`history_acceptance` inactive] -> `sc.legacy.partner.map`
      - 旧库报表承载清单 [`history_acceptance` inactive] -> `sc.legacy.report.inventory`
      - 旧库项目映射 [`history_acceptance` inactive] -> `sc.legacy.project.map`
      - 机械合同（合同） [`history_acceptance` inactive] -> `sc.legacy.direct.acceptance.fact`
      - 油卡登记 [`history_acceptance` inactive] -> `sc.legacy.fuel.card.fact`
      - 物料分类 [`history_acceptance` inactive] -> `sc.legacy.material.category`
      - 融资台账 [`history_acceptance` inactive] -> `sc.legacy.financing.loan.fact`
      - 账户收支来源明细 [`history_acceptance` inactive] -> `sc.legacy.account.transaction.line`
      - 账户管理 [`history_acceptance` inactive] -> `sc.fund.account`
      - 资金确认 [`history_acceptance` inactive] -> `sc.legacy.fund.confirmation.line`
    - 场景与能力 [`dev_governance`]
      - Scene Governance [`dev_governance`]
        - Company Channels [`dev_governance`] -> `sc.scene.company.channel`
        - Governance Actions [`dev_governance`] -> `sc.scene.governance.wizard`
        - Governance Logs [`dev_governance`] -> `sc.scene.governance.log`
      - 交付包安装记录 [`dev_governance`] -> `sc.pack.installation`
      - 交付包注册表 [`dev_governance`] -> `sc.pack.registry`
      - 场景版本 [`dev_governance`] -> `sc.scene.version`
      - 场景编排 [`dev_governance`] -> `sc.scene`
      - 能力分组 [`dev_governance`] -> `sc.capability.group`
      - 能力目录 [`dev_governance`] -> `sc.capability`
    - 工作流 [`dev_governance`]
      - 工作流定义 [`dev_governance`] -> `sc.workflow.def`
      - 工作流实例 [`dev_governance`] -> `sc.workflow.instance`
      - 工作流日志 [`dev_governance`] -> `sc.workflow.log`
      - 工作项 [`dev_governance`] -> `sc.workflow.workitem`
    - 用户优先入口迭代计划 [`system_config`] -> `sc.legacy.user.priority.menu.plan`
    - 用户信息与权限 [`system_config`] -> `res.users`
      - 历史角色投影 [`history_acceptance`] -> `sc.legacy.user.role`
      - 用户信息 [`history_acceptance`] -> `sc.legacy.user.profile`
      - 用户账号与权限 [`system_config`] -> `res.users`
      - 项目授权范围 [`history_acceptance`] -> `sc.legacy.user.project.scope`
    - 项目管理（后台） [`dev_governance`] -> `project.project`
  - 统计分析 [`formal_product`]
    - 业务核算主体 [`formal_product`] -> `sc.business.entity`
    - 客户供应商导入复核 [`formal_product`] -> `sc.partner.import.review`
    - 成本报表 [`formal_product`]
      - 发票分析报表 [`formal_product`] -> `sc.invoice.registration`
      - 发票分类汇总表 [`formal_product`] -> `sc.invoice.category.summary`
      - 工资统计表 [`formal_product`] -> `sc.salary.summary`
      - 库存统计表（新） [`formal_product`] -> `sc.material.stock.summary`
      - 成本统计表（综合） [`formal_product`] -> `sc.comprehensive.cost.summary`
      - 报销统计 [`formal_product`] -> `sc.expense.reimbursement.summary`
      - 账户收支统计表 [`formal_product` inactive] -> `sc.account.income.expense.summary`
      - 进项发票明细表 [`formal_product`] -> `sc.invoice.registration`
    - 经营分析 [`formal_product`]
      - 合同执行表 [`formal_product`] -> `construction.contract`
      - 项目经营分析 [`formal_product`] -> `sc.operating.metrics.project`
    - 财务分析 [`formal_product`]
      - 付款统计表 [`formal_product`] -> `sc.treasury.ledger`
      - 企业资金日报汇总 [`formal_product`] -> `sc.fund.daily.summary`
      - 供应商账款 [`formal_product`] -> `sc.ar.ap.company.summary`
      - 客户账款 [`formal_product`] -> `sc.ar.ap.project.summary`
      - 收款统计表 [`formal_product`] -> `sc.treasury.ledger`
      - 账户收支统计表 [`formal_product`] -> `sc.account.income.expense.summary`
      - 资金台账 [`formal_product`] -> `sc.treasury.ledger`
  - 财务中心 [`formal_product`]
    - 付款 [`formal_product` inactive]
      - 支付申请 [`formal_product` inactive] -> `payment.request`
    - 付款事实 [`formal_product` inactive]
      - 付款申请 [`formal_product` inactive] -> `payment.request`
      - 付款申请明细 [`formal_product` inactive] -> `payment.request.line`
      - 付款申请残余事实 [`formal_product` inactive] -> `sc.payment.execution`
    - 保证金管理 [`formal_product` inactive]
      - 付款保证金退回 [`formal_product`] -> `sc.expense.claim`
      - 付款还保证金 [`formal_product`] -> `sc.expense.claim`
      - 付款还保证金退回 [`formal_product`] -> `sc.expense.claim`
      - 保证金收取 [`formal_product`] -> `sc.expense.claim`
      - 自筹保证金 [`formal_product` inactive] -> `tender.guarantee`
      - 自筹保证金退回 [`formal_product` inactive] -> `tender.guarantee`
    - 借还款办理 [`formal_product` inactive]
    - 发票台账 [`formal_product`]
      - 发票总台账 [`formal_product`] -> `sc.invoice.registration`
      - 收款发票 [`formal_product`] -> `sc.receipt.invoice.line`
      - 进项发票 [`formal_product`] -> `sc.invoice.registration`
      - 销项发票 [`formal_product`] -> `sc.output.invoice.ledger`
      - 销项变更登记 [`formal_product`] -> `sc.output.invoice.adjustment`
      - 销项调整记录 [`formal_product`] -> `sc.output.invoice.ledger`
    - 待我审批（付款申请） [`formal_product` inactive] -> `tier.review`
    - 扣款 [`formal_product` inactive]
    - 扣款与非现金 [`formal_product`]
      - 扣款登记 [`formal_product`] -> `sc.expense.claim`
    - 收付款办理 [`formal_product`]
      - 公司财务支出 [`formal_product`] -> `sc.payment.execution`
      - 实付登记 [`formal_product`] -> `sc.payment.execution`
      - 工程进度款收入登记 [`formal_product`] -> `sc.receipt.income`
      - 往来单位付款 [`formal_product`] -> `sc.payment.execution`
      - 支付申请 [`formal_product`] -> `payment.request`
      - 收入 [`formal_product`] -> `sc.receipt.income`
      - 收款申请 [`formal_product`] -> `payment.request`
      - 收款登记 [`formal_product`] -> `sc.receipt.income`
      - 结算中心 [`formal_product`]
        - 结算单 [`formal_product`] -> `sc.settlement.order`
        - 结算调整 [`formal_product`] -> `sc.settlement.adjustment`
    - 收支 [`formal_product` inactive]
    - 收款 [`formal_product` inactive]
    - 费用与保证金 [`formal_product`] -> `sc.expense.claim`
      - 借款单 [`formal_product`] -> `sc.financing.loan`
      - 公司扣款 [`formal_product`] -> `sc.expense.claim`
      - 公司支出 [`formal_product`] -> `sc.payment.execution`
      - 公司收入 [`formal_product`] -> `sc.receipt.income`
      - 合同保证金支付 [`formal_product`] -> `sc.expense.claim`
      - 合同保证金退回 [`formal_product`] -> `sc.expense.claim`
      - 备用金 [`formal_product`] -> `sc.expense.claim`
      - 扣款实缴登记 [`formal_product`] -> `sc.expense.claim`
      - 扣款实缴退回 [`formal_product`] -> `sc.expense.claim`
      - 投标保证金支付 [`formal_product`] -> `sc.expense.claim`
      - 投标保证金退回 [`formal_product`] -> `sc.expense.claim`
      - 报销申请 [`formal_product`] -> `sc.expense.claim`
      - 费用报销单 [`formal_product`] -> `sc.expense.claim`
      - 还款单 [`formal_product`] -> `sc.expense.claim`
      - 项目费用报销单 [`formal_product`] -> `sc.expense.claim`
    - 资金分析 [`formal_product`]
      - 借款还款与调拨明细 [`formal_product`] -> `sc.interfund.movement.fact`
      - 公司-承包人资金责任余额 [`formal_product`] -> `sc.company.contractor.responsibility.summary`
      - 公司-承包人资金责任明细 [`formal_product`] -> `sc.company.contractor.responsibility.fact`
      - 往来对象资金总览 [`formal_product`] -> `sc.finance.counterparty.position.summary`
      - 项目与对象资金往来 [`formal_product`] -> `sc.finance.project.counterparty.position`
      - 项目借还调拨汇总 [`formal_product`] -> `sc.interfund.movement.project.summary`
      - 项目收付款来源明细 [`formal_product`] -> `sc.finance.business.fact`
      - 项目收付款汇总 [`formal_product`] -> `sc.finance.business.project.summary`
      - 项目资金总览 [`formal_product`] -> `sc.finance.project.capital.position`
    - 资金往来办理 [`formal_product`]
      - 企业资金日报 [`formal_product`] -> `sc.fund.daily.summary`
      - 余额调整 [`formal_product`] -> `sc.fund.account.operation`
      - 借款申请 [`formal_product`] -> `sc.financing.loan`
      - 借款申请 [`formal_product` inactive] -> `sc.financing.loan`
      - 承包人借项目款 [`formal_product`] -> `sc.financing.loan`
      - 承包人还项目款 [`formal_product`] -> `sc.expense.claim`
      - 自筹垫付办理 [`formal_product`] -> `sc.self.funding.registration`
      - 自筹退回办理 [`formal_product`] -> `sc.self.funding.registration`
      - 账户间资金往来 [`formal_product`] -> `sc.fund.account.operation`
      - 贷款登记 [`formal_product`] -> `sc.financing.loan`
      - 资金划拨 [`formal_product`] -> `sc.fund.account.operation`
      - 资金对账 [`formal_product`] -> `sc.treasury.reconciliation`
      - 资金日报表 [`formal_product`] -> `sc.fund.account.operation`
      - 资金调拨 [`formal_product`] -> `sc.fund.account.operation`
      - 还款登记 [`formal_product`] -> `sc.expense.claim`
      - 项目借公司款登记 [`formal_product`] -> `sc.financing.loan`
      - 项目还公司款登记 [`formal_product`] -> `sc.expense.claim`
    - 资金日报 [`formal_product` inactive]
    - 资金计划 [`formal_product`]
      - 资金计划汇总 [`formal_product`] -> `project.funding.baseline`
      - 资金计划申报 [`formal_product`] -> `project.funding.baseline`
    - 资金账户 [`formal_product` inactive]
    - 项目资金 [`formal_product` inactive]
  - 资料证照 [`formal_product`]
    - 借阅申请 [`formal_product`] -> `sc.document.admin.document`
    - 公司资料存档 [`formal_product`] -> `sc.document.admin.document`
    - 证照登记 [`formal_product`] -> `sc.document.admin.document`
  - 项目中心 [`formal_product`]
    - 投标管理 [`formal_product`]
      - 中标记录 [`formal_product`] -> `tender.bid`
      - 开标记录 [`formal_product`] -> `tender.opening`
      - 投标保证金 [`formal_product`] -> `tender.guarantee`
      - 投标准备 [`formal_product`] -> `tender.bid`
      - 投标报名管理 [`formal_product`] -> `tender.bid`
      - 投标报名费申请 [`formal_product`] -> `tender.doc.purchase`
      - 投标项目 [`formal_product`] -> `tender.bid`
    - 施工资料 [`formal_product`]
      - 现场资料 [`formal_product`] -> `sc.project.document`
    - 项目管理 [`formal_product`]
      - 工程结构 [`formal_product`] -> `construction.work.breakdown`
      - 工程结构 [`formal_product`] -> `sc.project.structure`
      - 快速创建项目 [`formal_product`] -> `project.project`
      - 执行结构 [`formal_product`] -> `ir.actions.server`
      - 项目台账 [`formal_product`] -> `project.project`
      - 项目看板 [`formal_product`] -> `project.project`
      - 项目立项 [`formal_product`] -> `project.project`
      - 项目资料 [`formal_product`] -> `sc.project.document`
      - 项目驾驶舱 [`formal_product`] -> `project.project`
    - 项目预算 [`formal_product`]
      - 工程量清单 [`formal_product`] -> `project.boq.line`
      - 预算清单 [`formal_product`] -> `project.budget`
  - 首页 [`formal_product`]
    - 我的审批 [`formal_product`] -> `sc.workbench.item`
    - 我的待办 [`formal_product`] -> `sc.workbench.item`
    - 我的项目 [`formal_product`] -> `project.project`
    - 角色首页 [`formal_product`] -> `scene:workspace.home`

## 待复核队列

未检测到需要人工复核的模糊菜单。
