# 产品菜单蓝图 V1

本蓝图由运行时菜单台账生成，用于回答“正式产品菜单长什么样”。历史验收、系统配置、开发治理不并入正式产品菜单，只作为边界列示。

## 当前结论

- 正式产品一级中心：`12` 个
- 正式产品 active 菜单：`237` 个
- 系统配置菜单：`30` 个，其中 active `30` 个
- 历史验收菜单：`194` 个，其中 active `142` 个
- 开发治理菜单：`30` 个，其中 active `30` 个
- 待复核菜单：`0` 个

## 正式产品一级中心

| 中心 | 正式子入口 | 历史验收子入口 | 系统配置子入口 | 隐藏项 | XMLID |
| --- | ---: | ---: | ---: | ---: | --- |
| 智慧大屏 | 6 | 0 | 0 | 1 | `smart_construction_core.menu_sc_projection_root` |
| 首页 | 4 | 0 | 0 | 0 | `smart_construction_core.menu_sc_workspace_center` |
| 项目中心 | 23 | 0 | 0 | 1 | `smart_construction_core.menu_sc_project_center` |
| 合同中心 | 22 | 0 | 0 | 7 | `smart_construction_core.menu_sc_contract_center` |
| 物资与分包 | 40 | 0 | 0 | 9 | `smart_construction_core.menu_sc_material_center` |
| 施工管理 | 10 | 0 | 0 | 0 | `smart_construction_core.menu_sc_construction_management_center` |
| 人事行政 | 8 | 0 | 0 | 1 | `smart_construction_core.menu_sc_hr_admin_center` |
| 资料证照 | 3 | 0 | 0 | 0 | `smart_construction_core.menu_sc_document_admin_center` |
| 成本中心 | 7 | 0 | 0 | 0 | `smart_construction_core.menu_sc_cost_center` |
| 财务中心 | 71 | 0 | 0 | 35 | `smart_construction_core.menu_sc_finance_center` |
| 税务中心 | 9 | 0 | 0 | 2 | `smart_construction_core.menu_sc_tax_center` |
| 统计分析 | 21 | 0 | 0 | 18 | `smart_construction_core.menu_sc_data_center` |

## 正式产品菜单结构

### 智慧大屏

- formal_active: `6`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 公司驾驶舱 -> `sc.operating.metrics.project`
- 项目驾驶舱 -> `project.project`
- 资金驾驶舱 -> `sc.dashboard.cockpit.fact`
- 成本驾驶舱 -> `sc.dashboard.cockpit.fact`
- 成本大屏 -> `sc.dashboard.cockpit.fact`
- 经营大屏 -> `sc.operating.metrics.project`

### 首页

- formal_active: `4`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 角色首页 -> `scene:workspace.home`
- 我的项目 -> `project.project`
- 我的待办 -> `sc.workbench.item`
- 我的审批 -> `sc.workbench.item`

### 项目中心

- formal_active: `23`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 项目管理
  - 项目立项 -> `project.project`
  - 快速创建项目 -> `project.project`
  - 项目台账 -> `project.project`
  - 执行结构 -> `ir.actions.server`
  - 项目看板 -> `project.project`
  - 项目驾驶舱 -> `project.project`
  - 项目资料 -> `sc.project.document`
  - 工程结构 -> `construction.work.breakdown`
  - 工程结构 -> `sc.project.structure`
- 投标管理
  - 投标项目 -> `tender.bid`
  - 投标准备 -> `tender.bid`
  - 投标报名管理 -> `tender.bid`
  - 投标报名费申请 -> `tender.doc.purchase`
  - 开标记录 -> `tender.opening`
  - 中标记录 -> `tender.bid`
  - 投标保证金 -> `tender.guarantee`
- 项目预算
  - 预算清单 -> `project.budget`
  - 工程量清单 -> `project.boq.line`
- 施工资料
  - 现场资料 -> `sc.project.document`

### 合同中心

- formal_active: `22`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 合同办理 -> `construction.contract`
- 收入合同台账 -> `sc.income.contract.ledger`
  - 收入合同台账 -> `sc.income.contract.ledger`
  - 项目收入合同 -> `construction.contract.income`
  - 施工合同 -> `construction.contract.income`
  - 收入合同签证 -> `sc.settlement.adjustment`
  - 收入合同执行 -> `construction.contract.income`
  - 收入合同结算 -> `sc.settlement.order`
  - 合同履约事件 -> `sc.contract.event`
- 支出合同台账 -> `sc.expense.contract.ledger`
  - 一般合同（公司） -> `sc.general.contract`
  - 支出合同台账 -> `sc.expense.contract.ledger`
  - 材料合同 -> `construction.contract.expense`
  - 正常合同 -> `construction.contract.expense`
  - 劳务合同 -> `construction.contract.expense`
  - 租赁合同 -> `construction.contract.expense`
  - 分包合同 -> `construction.contract.expense`
  - 其他合同 -> `construction.contract.expense`
  - 补充合同 -> `construction.contract.expense`
  - 支出合同签证 -> `sc.settlement.adjustment`
  - 支出合同执行 -> `construction.contract.expense`
  - 支出合同结算 -> `sc.settlement.order`

### 物资与分包

- formal_active: `40`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 物资管理
  - 材料档案 -> `sc.material.catalog`
  - 材料计划 -> `project.material.plan`
  - 采购申请 -> `sc.material.purchase.request`
  - 材料进场验收 -> `sc.material.acceptance`
  - 采购订单 -> `purchase.order`
  - 询比价 -> `sc.material.rfq`
  - 报价单 -> `sc.material.rfq`
  - 入库单 -> `sc.material.inbound`
  - 出库单 -> `sc.material.outbound`
  - 退库办理 -> `sc.material.outbound`
  - 材料调拨 -> `sc.material.outbound`
  - 材料损耗 -> `sc.material.outbound`
  - 材料价格库 -> `sc.material.price`
  - 材料结算 -> `sc.material.settlement`
- 劳务管理
  - 劳务计划 -> `sc.labor.plan`
  - 劳务申请 -> `sc.labor.request`
  - 考勤记录 -> `sc.attendance.checkin`
  - 方单 -> `sc.labor.usage`
  - 零星用工 -> `sc.labor.usage`
  - 劳务结算 -> `sc.labor.settlement`
- 机械设备
  - 设备计划 -> `sc.equipment.plan`
  - 设备申请 -> `sc.equipment.request`
  - 设备使用登记 -> `sc.equipment.usage`
  - 机械台班记录 -> `sc.equipment.usage`
  - 设备结算 -> `sc.equipment.settlement`
- 周转材料租赁
  - 租赁计划 -> `sc.material.rental.plan`
  - 租赁单 -> `sc.material.rental.order`
  - 租入 -> `sc.material.rental.order`
  - 还租 -> `sc.material.rental.order`
  - 租赁结算 -> `sc.material.rental.settlement`
- 专业分包
  - 分包计划 -> `sc.subcontract.plan`
  - 分包申请 -> `sc.subcontract.request`
  - 分包方单 -> `sc.subcontract.request`
  - 分包登记 -> `sc.subcontract.register`
  - 分包结算 -> `sc.subcontract.settlement`

### 施工管理

- formal_active: `10`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 进度管理 -> `project.progress.entry`
- 计划管理 -> `sc.plan`
- 计划汇报 -> `sc.plan.report`
- 施工日志 -> `sc.construction.diary`
- 质量检查 -> `sc.quality.issue`
- 质量整改 -> `sc.quality.rectification`
- 质量复验 -> `sc.quality.recheck`
- 安全检查 -> `sc.safety.issue`
- 安全整改 -> `sc.safety.rectification`
- 安全复验 -> `sc.safety.recheck`

### 人事行政

- formal_active: `8`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 请假/休假审批单 -> `sc.office.admin.document`
- 印章使用审批表 -> `sc.office.admin.document`
- 社保人员登记 -> `sc.hr.payroll.document`
- 社保登记 -> `sc.hr.payroll.document`
- 项目管理人员工资登记 -> `sc.hr.payroll.document`
- 工资登记 -> `sc.hr.payroll.document`
- 补助 -> `sc.hr.payroll.document`
- 奖金 -> `sc.hr.payroll.document`

### 资料证照

- formal_active: `3`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 证照登记 -> `sc.document.admin.document`
- 借阅申请 -> `sc.document.admin.document`
- 公司资料存档 -> `sc.document.admin.document`

### 成本中心

- formal_active: `7`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 目标成本 -> `project.budget`
- 预算清单分摊 -> `project.budget.cost.alloc`
- WBS/分部分项 -> `construction.work.breakdown`
- 进度计量 -> `project.progress.entry`
- 成本台账 -> `project.cost.ledger`
- 成本汇总 -> `project.cost.compare`
- 经营利润 -> `project.profit.compare`

### 财务中心

- formal_active: `71`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 收付款办理
  - 收入 -> `sc.receipt.income`
  - 收款登记 -> `sc.receipt.income`
  - 工程进度款收入登记 -> `sc.receipt.income`
  - 收款申请 -> `payment.request`
  - 支付申请 -> `payment.request`
  - 往来单位付款 -> `sc.payment.execution`
  - 结算中心
  - 实付登记 -> `sc.payment.execution`
  - 公司财务支出 -> `sc.payment.execution`
- 费用/保证金现金办理 -> `sc.expense.claim`
  - 报销申请 -> `sc.expense.claim`
  - 费用报销单 -> `sc.expense.claim`
  - 项目费用报销单 -> `sc.expense.claim`
  - 扣款实缴登记 -> `sc.expense.claim`
  - 公司扣款 -> `sc.expense.claim`
  - 扣款实缴退回 -> `sc.expense.claim`
  - 公司收入 -> `sc.receipt.income`
  - 投标保证金支付 -> `sc.expense.claim`
  - 投标保证金退回 -> `sc.expense.claim`
  - 公司支出 -> `sc.payment.execution`
  - 合同保证金支付 -> `sc.expense.claim`
  - 合同保证金退回 -> `sc.expense.claim`
  - 备用金 -> `sc.expense.claim`
  - 借款单 -> `sc.financing.loan`
  - 还款单 -> `sc.expense.claim`
- 资金计划
  - 资金计划申报 -> `project.funding.baseline`
  - 资金计划汇总 -> `project.funding.baseline`
- 非现金业务管理
  - 扣款登记 -> `sc.expense.claim`
- 资金往来办理
  - 借款申请 -> `sc.financing.loan`
  - 还款登记 -> `sc.expense.claim`
  - 承包人还项目款 -> `sc.expense.claim`
  - 资金对账 -> `sc.treasury.reconciliation`
  - 承包人借项目款 -> `sc.financing.loan`
  - 项目借公司款登记 -> `sc.financing.loan`
  - 项目还公司款登记 -> `sc.expense.claim`
  - 贷款登记 -> `sc.financing.loan`
  - 自筹垫付办理 -> `sc.self.funding.registration`
  - 自筹退回办理 -> `sc.self.funding.registration`
  - 企业资金日报 -> `sc.fund.daily.summary`
  - 账户间资金往来 -> `sc.fund.account.operation`
  - 资金划拨 -> `sc.fund.account.operation`
  - 资金调拨 -> `sc.fund.account.operation`
  - 余额调整 -> `sc.fund.account.operation`
  - 资金日报表 -> `sc.fund.account.operation`
- 发票台账
  - 发票总台账 -> `sc.invoice.registration`
  - 销项发票 -> `sc.output.invoice.ledger`
  - 销项变更登记 -> `sc.output.invoice.adjustment`
  - 销项调整记录 -> `sc.output.invoice.ledger`
  - 进项发票 -> `sc.invoice.registration`
  - 收款发票 -> `sc.receipt.invoice.line`
- 资金往来分析
  - 项目资金总览 -> `sc.finance.project.capital.position`
  - 往来对象资金总览 -> `sc.finance.counterparty.position.summary`
  - 项目与对象资金往来 -> `sc.finance.project.counterparty.position`
  - 公司-承包人资金责任余额 -> `sc.company.contractor.responsibility.summary`
  - 公司-承包人资金责任明细 -> `sc.company.contractor.responsibility.fact`
  - 项目收付款汇总 -> `sc.finance.business.project.summary`
  - 项目借还调拨汇总 -> `sc.interfund.movement.project.summary`
  - 项目收付款来源明细 -> `sc.finance.business.fact`
  - 借款还款与调拨明细 -> `sc.interfund.movement.fact`

### 税务中心

- formal_active: `9`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 财税报表
  - 项目经营统计表 -> `sc.operating.metrics.project`
  - 公司经营情况表 -> `sc.company.operation.summary`
- 开票与税务办理
  - 销项开票申请 -> `sc.invoice.registration`
  - 销项开票登记 -> `sc.invoice.registration`
  - 预缴税款 -> `sc.invoice.registration`
  - 进项税额上报 -> `sc.invoice.registration`
  - 抵扣登记 -> `sc.tax.deduction.registration`

### 统计分析

- formal_active: `21`
- history_active_under_center: `0`
- system_config_active_under_center: `0`

- 经营分析
  - 项目经营分析 -> `sc.operating.metrics.project`
  - 合同执行表 -> `construction.contract`
- 业务核算主体 -> `sc.business.entity`
- 成本报表
  - 库存统计表（新） -> `sc.material.stock.summary`
  - 成本统计表（综合） -> `sc.comprehensive.cost.summary`
  - 进项发票明细表 -> `sc.invoice.registration`
  - 发票分析报表 -> `sc.invoice.registration`
  - 发票分类汇总表 -> `sc.invoice.category.summary`
  - 报销统计 -> `sc.expense.reimbursement.summary`
  - 工资统计表 -> `sc.salary.summary`
- 客户供应商导入复核 -> `sc.partner.import.review`
- 财务分析
  - 客户账款 -> `sc.ar.ap.project.summary`
  - 供应商账款 -> `sc.ar.ap.company.summary`
  - 收款统计表 -> `sc.treasury.ledger`
  - 付款统计表 -> `sc.treasury.ledger`
  - 账户收支统计表 -> `sc.account.income.expense.summary`
  - 资金台账 -> `sc.treasury.ledger`
  - 企业资金日报汇总 -> `sc.fund.daily.summary`

## 系统配置边界

- 智慧施工管理平台 / 基础设置

## 历史验收边界

- 智慧施工管理平台 / 用户核对菜单
- 智慧施工管理平台 / 用户验收

## 开发治理边界

- 平台内核
- 平台内核 / 产品发布
- 平台内核 / 公司访问

## 混入正式中心的历史入口

这些入口仍挂在正式产品中心下，但分类属于历史验收。下一步应逐项决定：迁到用户验收/用户核对入口、转成正式产品入口，或隐藏。

无。

## 收口信号

- 当前无待复核菜单。
- 当前无独立用户配置入口；低代码和产品配置仍归入系统配置边界。
