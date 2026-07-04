# 完整产品办理能力口径 V1

本报告不只按当前发布导航计数，而是同时读取产品策略与 Odoo 原生菜单动作，区分已发布正式办理能力、已建模但未纳入发布面的办理能力、历史验收/来源入口，以及查询分析配置入口。

## 口径

- 已发布正式办理能力：产品策略中 `entry_intent=handling` 且已发布、启用的入口。
- 已建模未发布办理能力：原生产品菜单下存在动作和业务模型，名称/路径呈现办理语义，但未进入当前产品策略发布面。
- 历史验收/来源入口：用户核对、用户验收、legacy/source fact 类入口，不直接等同正式产品办理能力。
- 查询分析配置入口：台账、报表、统计、大屏、配置、字典、治理等非办理入口。

## 摘要

- 已发布正式办理能力：`81`
- 产品策略中已建模但未发布：`0`
- 原生菜单中已建模但未纳入发布面的办理能力：`0`
- 历史验收/来源入口：`89`
- 查询分析配置入口：`22`
- 待人工复核入口：`0`

## 已发布正式办理能力

| 中心 | 业务域 | 能力入口 | 模型 | XMLID |
| --- | --- | --- | --- | --- |
| 项目中心 |  | 投标报名管理 | `tender.bid` | `smart_construction_core.menu_sc_tender_registration` |
| 项目中心 |  | 投标报名费申请 | `tender.doc.purchase` | `smart_construction_core.menu_sc_tender_registration_fee` |
| 合同中心 | 变更签证 | 支出合同签证 | `sc.settlement.adjustment` | `smart_construction_core.menu_sc_expense_contract_variation` |
| 合同中心 | 变更签证 | 收入合同签证 | `sc.settlement.adjustment` | `smart_construction_core.menu_sc_income_contract_variation` |
| 合同中心 | 合同管理 | 一般合同（公司） | `sc.general.contract` | `smart_construction_core.menu_sc_general_contract` |
| 合同中心 | 合同管理 | 施工合同 | `construction.contract` | `smart_construction_core.menu_sc_construction_contract` |
| 合同中心 | 结算管理 | 支出合同结算 | `sc.settlement.order` | `smart_construction_core.menu_sc_expense_contract_settlement` |
| 合同中心 | 结算管理 | 收入合同结算 | `sc.settlement.order` | `smart_construction_core.menu_sc_income_contract_settlement` |
| 施工管理 |  | 施工日志 | `sc.construction.diary` | `smart_construction_core.menu_sc_construction_diary` |
| 施工管理 | 计划进度 | 计划汇报 | `sc.plan.report` | `smart_construction_core.menu_sc_plan_report` |
| 施工管理 | 计划进度 | 计划管理 | `sc.plan` | `smart_construction_core.menu_sc_plan` |
| 物资与分包 |  | 材料计划 | `project.material.plan` | `smart_construction_core.menu_project_material_plan` |
| 物资与分包 | 分包管理 | 分包方单 | `sc.subcontract.request` | `smart_construction_core.menu_sc_subcontract_request_acceptance` |
| 物资与分包 | 分包管理 | 分包申请 | `sc.subcontract.request` | `smart_construction_core.menu_sc_subcontract_request` |
| 物资与分包 | 分包管理 | 分包登记 | `sc.subcontract.register` | `smart_construction_core.menu_sc_subcontract_register` |
| 物资与分包 | 分包管理 | 分包结算 | `sc.subcontract.settlement` | `smart_construction_core.menu_sc_subcontract_settlement` |
| 物资与分包 | 分包管理 | 分包计划 | `sc.subcontract.plan` | `smart_construction_core.menu_sc_subcontract_plan` |
| 物资与分包 | 劳务管理 | 劳务申请 | `sc.labor.request` | `smart_construction_core.menu_sc_labor_request` |
| 物资与分包 | 劳务管理 | 劳务结算 | `sc.labor.settlement` | `smart_construction_core.menu_sc_labor_settlement` |
| 物资与分包 | 劳务管理 | 劳务计划 | `sc.labor.plan` | `smart_construction_core.menu_sc_labor_plan` |
| 物资与分包 | 劳务管理 | 方单 | `sc.labor.usage` | `smart_construction_core.menu_sc_labor_usage_acceptance` |
| 物资与分包 | 劳务管理 | 考勤记录 | `sc.attendance.checkin` | `smart_construction_core.menu_sc_attendance_checkin` |
| 物资与分包 | 劳务管理 | 零星用工 | `sc.labor.usage` | `smart_construction_core.menu_sc_labor_casual_acceptance` |
| 物资与分包 | 机械管理 | 机械台班记录 | `sc.equipment.usage` | `smart_construction_core.menu_sc_equipment_shift_acceptance` |
| 物资与分包 | 机械管理 | 设备使用登记 | `sc.equipment.usage` | `smart_construction_core.menu_sc_equipment_usage` |
| 物资与分包 | 机械管理 | 设备申请 | `sc.equipment.request` | `smart_construction_core.menu_sc_equipment_request` |
| 物资与分包 | 机械管理 | 设备结算 | `sc.equipment.settlement` | `smart_construction_core.menu_sc_equipment_settlement` |
| 物资与分包 | 机械管理 | 设备计划 | `sc.equipment.plan` | `smart_construction_core.menu_sc_equipment_plan` |
| 物资与分包 | 材料管理 | 入库单 | `sc.material.inbound` | `smart_construction_core.menu_sc_material_inbound` |
| 物资与分包 | 材料管理 | 出库单 | `sc.material.outbound` | `smart_construction_core.menu_sc_material_outbound` |
| 物资与分包 | 材料管理 | 采购订单 | `purchase.order` | `smart_construction_core.menu_sc_purchase_order` |
| 物资与分包 | 询价报价 | 报价单 | `sc.material.rfq` | `smart_construction_core.menu_sc_material_quote_acceptance` |
| 财务中心 | 付款管理 | 公司财务支出 | `sc.payment.execution` | `smart_construction_core.menu_sc_company_finance_expense` |
| 财务中心 | 付款管理 | 实付登记 | `sc.payment.execution` | `smart_construction_core.menu_sc_payment_execution` |
| 财务中心 | 付款管理 | 往来单位付款 | `sc.payment.execution` | `smart_construction_core.menu_sc_partner_payment` |
| 财务中心 | 付款管理 | 支付申请 | `payment.request` | `smart_construction_core.menu_sc_user_payment_apply_acceptance` |
| 财务中心 | 借还款 | 借款申请 | `sc.financing.loan` | `smart_construction_core.menu_sc_borrowing_request` |
| 财务中心 | 借还款 | 承包人借项目款 | `sc.financing.loan` | `smart_construction_core.menu_sc_contractor_project_borrow` |
| 财务中心 | 借还款 | 承包人还项目款 | `sc.expense.claim` | `smart_construction_core.menu_sc_contractor_project_repay` |
| 财务中心 | 借还款 | 还款登记 | `sc.expense.claim` | `smart_construction_core.menu_sc_repayment_registration` |
| 财务中心 | 借还款 | 项目借公司款登记 | `sc.financing.loan` | `smart_construction_core.menu_sc_project_borrow_company` |
| 财务中心 | 借还款 | 项目还公司款登记 | `sc.expense.claim` | `smart_construction_core.menu_sc_project_repay_company` |
| 财务中心 | 扣款与非现金 | 扣款登记 | `sc.expense.claim` | `smart_construction_core.menu_sc_deduction_bill` |
| 财务中心 | 收款管理 | 工程进度款收入登记 | `sc.receipt.income` | `smart_construction_core.menu_sc_engineering_progress_income` |
| 财务中心 | 收款管理 | 收入 | `sc.receipt.income` | `smart_construction_core.menu_sc_user_income` |
| 财务中心 | 收款管理 | 收款申请 | `payment.request` | `smart_construction_core.menu_payment_request_receive` |
| 财务中心 | 收款管理 | 收款登记 | `sc.receipt.income` | `smart_construction_core.menu_sc_receipt_income` |
| 财务中心 | 结算管理 | 结算单 | `sc.settlement.order` | `smart_construction_core.menu_sc_settlement_order` |
| 财务中心 | 结算管理 | 结算调整 | `sc.settlement.adjustment` | `smart_construction_core.menu_sc_settlement_adjustment` |
| 财务中心 | 自筹资金 | 自筹垫付收入 | `sc.self.funding.registration` | `smart_construction_core.menu_sc_self_funding_advance_income` |
| 财务中心 | 自筹资金 | 自筹退回 | `sc.self.funding.registration` | `smart_construction_core.menu_sc_self_funding_advance_refund` |
| 财务中心 | 账户资金 | 账户间资金往来 | `sc.fund.account.operation` | `smart_construction_core.menu_sc_fund_account_between_user` |
| 财务中心 | 账户资金 | 资金对账 | `sc.treasury.reconciliation` | `smart_construction_core.menu_sc_treasury_reconciliation` |
| 财务中心 | 费用与保证金 | 付款保证金退回 | `sc.expense.claim` | `smart_construction_core.menu_sc_payment_deposit_refund` |
| 财务中心 | 费用与保证金 | 付款还保证金 | `sc.expense.claim` | `smart_construction_core.menu_sc_payment_deposit_return` |
| 财务中心 | 费用与保证金 | 付款还保证金退回 | `sc.expense.claim` | `smart_construction_core.menu_sc_payment_deposit_return_refund_formal` |
| 财务中心 | 费用与保证金 | 合同保证金支付 | `sc.expense.claim` | `smart_construction_core.menu_sc_contract_deposit_register` |
| 财务中心 | 费用与保证金 | 合同保证金退回 | `sc.expense.claim` | `smart_construction_core.menu_sc_contract_deposit_return` |
| 财务中心 | 费用与保证金 | 扣款实缴登记 | `sc.expense.claim` | `smart_construction_core.menu_sc_deduction_paid` |
| 财务中心 | 费用与保证金 | 扣款实缴退回 | `sc.expense.claim` | `smart_construction_core.menu_sc_deduction_paid_refund` |
| 财务中心 | 费用与保证金 | 投标保证金支付 | `sc.expense.claim` | `smart_construction_core.menu_sc_bid_deposit_pay` |
| 财务中心 | 费用与保证金 | 投标保证金退回 | `sc.expense.claim` | `smart_construction_core.menu_sc_bid_deposit_return` |
| 财务中心 | 费用与保证金 | 报销申请 | `sc.expense.claim` | `smart_construction_core.menu_sc_reimbursement_request` |
| 财务中心 | 费用与保证金 | 费用报销单 | `sc.expense.claim` | `smart_construction_core.menu_sc_expense_claim` |
| 财务中心 | 费用与保证金 | 项目费用报销单 | `sc.expense.claim` | `smart_construction_core.menu_sc_project_expense_claim` |
| 人事行政 |  | 社保人员登记 | `sc.hr.payroll.document` | `smart_construction_core.menu_sc_social_person_registration` |
| 人事行政 |  | 社保登记 | `sc.hr.payroll.document` | `smart_construction_core.menu_sc_social_registration` |
| 人事行政 |  | 补助 | `sc.hr.payroll.document` | `smart_construction_core.menu_sc_subsidy` |
| 人事行政 |  | 项目管理人员工资登记 | `sc.hr.payroll.document` | `smart_construction_core.menu_sc_salary_registration_scbs55_formal` |
| 人事行政 | 薪资福利 | 奖金 | `sc.hr.payroll.document` | `smart_construction_core.menu_sc_bonus` |
| 人事行政 | 行政审批 | 印章使用审批表 | `sc.office.admin.document` | `smart_construction_core.menu_sc_seal_use_request` |
| 人事行政 | 请假 | 请假/休假审批单 | `sc.office.admin.document` | `smart_construction_core.menu_sc_leave_request` |
| 资料证照 |  | 公司资料存档 | `sc.document.admin.document` | `smart_construction_core.menu_sc_company_document_archive` |
| 资料证照 | 证照管理 | 证照登记 | `sc.document.admin.document` | `smart_construction_core.menu_sc_certificate_registration` |
| 资料证照 | 资料借阅 | 借阅申请 | `sc.document.admin.document` | `smart_construction_core.menu_sc_document_borrow` |
| 税务中心 |  | 外经证登记 | `sc.legacy.payment.residual.fact` | `smart_construction_core.menu_sc_tax_certificate_registration_user` |
| 税务中心 |  | 抵扣登记 | `sc.tax.deduction.registration` | `smart_construction_core.menu_sc_tax_deduction_registration_user` |
| 税务中心 |  | 进项发票 | `sc.invoice.registration` | `smart_construction_core.menu_sc_invoice_input` |
| 税务中心 |  | 销项开票申请 | `sc.invoice.registration` | `smart_construction_core.menu_sc_invoice_application_user` |
| 税务中心 |  | 销项开票登记 | `sc.invoice.registration` | `smart_construction_core.menu_sc_invoice_registration_user` |
| 税务中心 |  | 预缴税款 | `sc.invoice.registration` | `smart_construction_core.menu_sc_invoice_prepaid_tax_user` |

## 已建模但未纳入发布面的办理能力

无。

## 待人工复核入口

无。

## 历史验收/来源入口边界

这些入口用于历史数据承载、核对或来源追溯；只有吸收到正式模型和正式产品菜单后，才算正式办理能力。

| 中心 | 业务域 | 能力入口 | 模型 | 状态 | XMLID |
| --- | --- | --- | --- | --- | --- |
| 用户核对菜单 | 人事行政 | 印章使用审批表 | `sc.office.admin.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_060_印章使用审批表` |
| 用户核对菜单 | 人事行政 | 奖金 | `sc.hr.payroll.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_130_奖金` |
| 用户核对菜单 | 人事行政 | 工资登记 | `sc.hr.payroll.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_110_工资登记` |
| 用户核对菜单 | 人事行政 | 社保人员登记 | `sc.hr.payroll.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_090_社保人员登记` |
| 用户核对菜单 | 人事行政 | 社保登记 | `sc.hr.payroll.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_100_社保登记` |
| 用户核对菜单 | 人事行政 | 补助 | `sc.hr.payroll.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_120_补助` |
| 用户核对菜单 | 人事行政 | 请假/休假审批单 | `sc.office.admin.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_050_请假_休假审批单` |
| 用户核对菜单 | 付款 | 往来单位付款 | `sc.payment.execution` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_310_往来单位付款` |
| 用户核对菜单 | 付款 | 支付申请 | `payment.request` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_290_支付申请` |
| 用户核对菜单 | 分析大屏 | 成本大屏 | `sc.dashboard.cockpit.fact` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_540_成本大屏` |
| 用户核对菜单 | 分析大屏 | 经营大屏 | `sc.operating.metrics.project` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_550_经营大屏` |
| 用户核对菜单 | 办公资料 | 公司资料存档 | `sc.document.admin.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_040_公司资料存档` |
| 用户核对菜单 | 发票税务 | 外经证登记 | `sc.legacy.payment.residual.fact` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_440_外经证登记` |
| 用户核对菜单 | 发票税务 | 开票申请 | `sc.invoice.registration` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_390_开票申请` |
| 用户核对菜单 | 发票税务 | 开票登记 | `sc.invoice.registration` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_400_开票登记` |
| 用户核对菜单 | 发票税务 | 抵扣登记 | `sc.tax.deduction.registration` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_430_抵扣登记` |
| 用户核对菜单 | 发票税务 | 进项上报 | `sc.legacy.invoice.tax.fact` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_420_进项上报` |
| 用户核对菜单 | 发票税务 | 预缴税款 | `sc.invoice.registration` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_410_预缴税款` |
| 用户核对菜单 | 合同 | 施工合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_030_施工合同` |
| 用户核对菜单 | 基础资料 | 供应商/合作单位 | `sc.business.entity` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_010_供应商_合作单位` |
| 用户核对菜单 | 基础资料 | 往来单位 | `sc.business.entity` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_020_往来单位` |
| 用户核对菜单 | 成本报表 | 供货合同分析 | `sc.legacy.supplier.contract.pricing.fact` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_450_供货合同分析` |
| 用户核对菜单 | 成本报表 | 发票分析报表 | `sc.invoice.analysis.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_510_发票分析报表` |
| 用户核对菜单 | 成本报表 | 发票成本进度报表 | `sc.invoice.cost.progress.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_500_发票成本进度报表` |
| 用户核对菜单 | 成本报表 | 库存统计表（新） | `sc.material.stock.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_460_库存统计表_新` |
| 用户核对菜单 | 成本报表 | 成本统计表（综合） | `sc.comprehensive.cost.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_480_成本统计表_综合` |
| 用户核对菜单 | 成本报表 | 投标保证金报表 | `sc.tender.guarantee.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_490_投标保证金报表` |
| 用户核对菜单 | 成本报表 | 账户收支统计表 | `sc.account.income.expense.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_470_账户收支统计表` |
| 用户核对菜单 | 扣款 | 扣款单 | `sc.tax.deduction.registration` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_300_扣款单` |
| 用户核对菜单 | 扣款 | 扣款实缴登记 | `sc.expense.claim` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_330_扣款实缴登记` |
| 用户核对菜单 | 扣款 | 扣款实缴退回 | `sc.expense.claim` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_340_扣款实缴退回` |
| 用户核对菜单 | 投标 | 投标报名管理 | `tender.bid` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_160_投标报名管理` |
| 用户核对菜单 | 投标 | 投标报名费申请 | `tender.doc.purchase` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_170_投标报名费申请` |
| 用户核对菜单 | 收支 | 公司财务支出 | `sc.expense.claim` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_260_公司财务支出` |
| 用户核对菜单 | 收支 | 收入 | `sc.receipt.income` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_250_收入` |
| 用户核对菜单 | 收款 | 到款确认表 | `sc.legacy.fund.confirmation.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_350_到款确认表` |
| 用户验收 | 直营项目系统菜单 | 供货合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_supplier_contract` |
| 用户验收 | 直营项目系统菜单 | 供货合同（数据） | `sc.legacy.supplier.contract.pricing.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_supplier_contract_current` |
| 用户验收 | 直营项目系统菜单 | 充值登记 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_fuel_recharge` |
| 用户验收 | 直营项目系统菜单 | 入库 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_material_inbound` |
| 用户验收 | 直营项目系统菜单 | 分包合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_subcontract_contract` |
| 用户验收 | 直营项目系统菜单 | 分包方单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_subcontract_request` |
| 用户验收 | 直营项目系统菜单 | 分包结算单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_subcontract_settlement` |
| 用户验收 | 直营项目系统菜单 | 加油登记 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_fuel_refuel` |
| 用户验收 | 直营项目系统菜单 | 劳务合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_labor_contract` |
| 用户验收 | 直营项目系统菜单 | 劳务结算 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_labor_settlement` |
| 用户验收 | 直营项目系统菜单 | 工程结算单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_settlement_order` |
| 用户验收 | 直营项目系统菜单 | 工程进度收款 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_engineering_progress_receipt` |
| 用户验收 | 直营项目系统菜单 | 库存统计表（新） | `sc.material.stock.summary` | native_active | `smart_construction_core.menu_scbsly_acceptance_material_stock` |
| 用户验收 | 直营项目系统菜单 | 往来单位付款 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_partner_payment` |
| 用户验收 | 直营项目系统菜单 | 总包进项上报 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_general_contract_input_tax_report` |
| 用户验收 | 直营项目系统菜单 | 成本统计表（数据） | `sc.comprehensive.cost.summary` | native_active | `smart_construction_core.menu_scbsly_acceptance_comprehensive_cost` |
| 用户验收 | 直营项目系统菜单 | 报价单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_material_quote` |
| 用户验收 | 直营项目系统菜单 | 支付申请 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_payment_apply` |
| 用户验收 | 直营项目系统菜单 | 方单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_labor_usage` |
| 用户验收 | 直营项目系统菜单 | 施工合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_construction_contract` |
| 用户验收 | 直营项目系统菜单 | 施工日志（新） | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_construction_diary` |
| 用户验收 | 直营项目系统菜单 | 机械台班记录 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_equipment_shift` |
| 用户验收 | 直营项目系统菜单 | 机械合同（合同） | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_equipment_contract` |
| 用户验收 | 直营项目系统菜单 | 机械结算单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_equipment_settlement` |
| 用户验收 | 直营项目系统菜单 | 材料结算单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_material_settlement` |
| 用户验收 | 直营项目系统菜单 | 材料计划 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_material_plan` |
| 用户验收 | 直营项目系统菜单 | 油卡登记 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_fuel_card` |
| 用户验收 | 直营项目系统菜单 | 租入 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_rental_in` |
| 用户验收 | 直营项目系统菜单 | 租赁合同 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_rental_contract` |
| 用户验收 | 直营项目系统菜单 | 租赁结算单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_rental_settlement` |
| 用户验收 | 直营项目系统菜单 | 管理人员工资表 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_salary` |
| 用户验收 | 直营项目系统菜单 | 还租 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_rental_return` |
| 用户验收 | 直营项目系统菜单 | 进项上报 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_input_tax_report` |
| 用户验收 | 直营项目系统菜单 | 零星用工 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_labor_casual` |
| 用户验收 | 直营项目系统菜单 | 项目费用报销单 | `sc.legacy.direct.acceptance.fact` | native_active | `smart_construction_core.menu_scbsly_acceptance_project_expense` |
| 用户核对菜单 | 组织人员 | 公司人员名册（配置） | `sc.legacy.user.profile` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_080_公司人员名册_配置` |
| 用户核对菜单 | 组织人员 | 组织机构 | `hr.department` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_070_组织机构` |
| 用户核对菜单 | 证照资料 | 借阅申请 | `sc.document.admin.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_150_借阅申请` |
| 用户核对菜单 | 证照资料 | 证照登记 | `sc.document.admin.document` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_140_证照登记` |
| 用户核对菜单 | 财税报表 | 应收应付报表 | `sc.ar.ap.report.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_530_应收应付报表` |
| 用户核对菜单 | 财税报表 | 项目经营统计表 | `sc.project.operation.summary` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_520_项目经营统计表` |
| 用户核对菜单 | 费用报销 | 报销申请 | `sc.expense.claim` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_240_报销申请` |
| 用户核对菜单 | 资金保证金 | 付款还保证金 | `tender.guarantee` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_200_付款还保证金` |
| 用户核对菜单 | 资金保证金 | 付款还保证金退回 | `tender.guarantee` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_210_付款还保证金退回` |
| 用户核对菜单 | 资金借还 | 借款申请 | `sc.financing.loan` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_220_借款申请` |
| 用户核对菜单 | 资金借还 | 还款登记 | `sc.financing.loan` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_230_还款登记` |
| 用户核对菜单 | 资金日报 | 资金日报表 | `sc.legacy.fund.daily.line` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_360_资金日报表` |
| 用户核对菜单 | 资金账户 | 账户间资金往来 | `sc.fund.account.operation` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_320_账户间资金往来` |
| 用户核对菜单 | 项目台账（公司 | 项目台账（公司/项目/经营方式） | `project.project` | native_active | `smart_construction_core.menu_sc_acceptance_project_ledger` |
| 用户核对菜单 | 项目资金 | 承包人借项目款 | `sc.financing.loan` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_280_承包人借项目款` |
| 用户核对菜单 | 项目资金 | 承包人还项目款 | `sc.expense.claim` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_270_承包人还项目款` |
| 用户核对菜单 | 项目资金 | 项目借公司款登记 | `sc.financing.loan` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_370_项目借公司款登记` |
| 用户核对菜单 | 项目资金 | 项目还公司款登记 | `sc.financing.loan` | native_active | `smart_construction_core.menu_scbs55_user_acceptance_380_项目还公司款登记` |
