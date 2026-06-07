# 用户确认菜单表单能力审计

- 产品：`construction.standard`
- 菜单数：62
- 阻断项：0
- 需复核：0
- 通过：62

| 分组 | 菜单 | 模型 | 严重度 | 缺口 | 列表字段未进表单 | 表单按钮 |
| --- | --- | --- | --- | --- | --- | --- |
| 基础资料 | 客户 | `res.partner` | ok | - | - | action_open_sc_partner_business_fact_lines, action_open_source_record |
| 基础资料 | 供应商 | `res.partner` | ok | - | - | action_open_sc_partner_business_fact_lines, action_open_source_record |
| 项目中心 | 项目台账 | `project.project` | ok | - | - | 556, action_sc_submit, action_view_stage_requirements, 577, 512, 673, action_view_my_tasks |
| 项目中心 | 投标报名管理 | `tender.bid` | ok | - | - | action_to_estimating, action_to_submitted, action_to_waiting, action_mark_won, action_mark_lost, action_to_prepare, 514 |
| 项目中心 | 投标报名费申请 | `tender.doc.purchase` | ok | - | - | action_submit, action_approve, action_reject, action_reset_draft |
| 合同中心 | 一般合同（公司） | `sc.general.contract` | ok | - | - | action_confirm, validate_tier, reject_tier |
| 合同中心 | 补充合同 | `construction.contract.expense` | ok | - | - | action_generate_lines_from_budget, action_confirm, validate_tier, reject_tier, action_reset_draft |
| 合同中心 | 收入合同执行 | `construction.contract.income` | ok | - | - | action_generate_lines_from_budget, action_confirm, validate_tier, reject_tier, action_reset_draft |
| 合同中心 | 支出合同执行 | `construction.contract.expense` | ok | - | - | action_generate_lines_from_budget, action_confirm, validate_tier, reject_tier, action_reset_draft |
| 合同中心 | 收入合同结算 | `sc.settlement.order` | ok | - | - | action_submit |
| 合同中心 | 支出合同结算 | `sc.settlement.order` | ok | - | - | action_submit |
| 施工管理 | 施工日志 | `sc.construction.diary` | ok | - | - | action_confirm, action_done, action_cancel |
| 物资与分包 | 材料计划 | `project.material.plan` | ok | - | - | action_submit, validate_tier, reject_tier, action_view_purchase_orders, action_view_purchase_lines |
| 物资与分包 | 租入 | `sc.legacy.direct.acceptance.fact` | ok | - | - | - |
| 物资与分包 | 分包方单 | `sc.subcontract.request` | ok | - | - | action_submit, action_approve, action_reset_draft, action_cancel |
| 物资与分包 | 还租 | `sc.legacy.direct.acceptance.fact` | ok | - | - | - |
| 物资与分包 | 方单 | `sc.labor.usage` | ok | - | - | action_submit, action_confirm, action_reset_draft, action_cancel |
| 物资与分包 | 机械台班记录 | `sc.equipment.usage` | ok | - | - | action_submit, action_confirm, action_reset_draft, action_cancel |
| 物资与分包 | 零星用工 | `sc.labor.usage` | ok | - | - | action_submit, action_confirm, action_reset_draft, action_cancel |
| 物资与分包 | 报价单 | `sc.material.rfq` | ok | - | - | action_submit, action_select, action_create_purchase_order, action_reset_draft, action_cancel |
| 物资与分包 | 入库单 | `sc.material.inbound` | ok | - | - | action_submit, action_receive, action_reset_draft, action_cancel, action_load_acceptance_lines |
| 物资与分包 | 出库单 | `sc.material.outbound` | ok | - | - | action_submit, action_issue, action_reset_draft, action_cancel |
| 财务中心 | 收入 | `sc.receipt.income` | ok | - | - | action_confirm, validate_tier, reject_tier, action_received, action_cancel |
| 财务中心 | 承包人还项目款 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 扣款单 | `sc.tax.deduction.registration` | ok | - | - | action_confirm, action_deduct, action_cancel |
| 财务中心 | 到款确认表 | `sc.legacy.fund.confirmation.document` | ok | - | - | - |
| 财务中心 | 资金日报表 | `sc.fund.account.operation` | ok | - | - | action_confirm, action_done, action_cancel, action_reset_draft |
| 财务中心 | 报销申请 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 工程进度款收入登记 | `sc.receipt.income` | ok | - | - | action_confirm, validate_tier, reject_tier, action_received, action_cancel |
| 财务中心 | 付款还保证金退回 | `tender.guarantee` | ok | - | - | action_confirm, action_cancel, action_reset_draft |
| 财务中心 | 公司财务支出 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 承包人借项目款 | `sc.financing.loan` | ok | - | - | action_confirm, validate_tier, reject_tier, action_done, action_cancel |
| 财务中心 | 扣款实缴登记 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 支付申请 | `payment.request` | ok | - | - | action_submit |
| 财务中心 | 进项发票 | `sc.invoice.registration` | ok | - | - | action_confirm, validate_tier, reject_tier, action_register, action_cancel |
| 财务中心 | 预缴税款 | `sc.invoice.registration` | ok | - | - | action_confirm, validate_tier, reject_tier, action_register, action_cancel |
| 财务中心 | 项目借公司款登记 | `sc.financing.loan` | ok | - | - | action_confirm, validate_tier, reject_tier, action_done, action_cancel |
| 财务中心 | 扣款实缴退回 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 项目费用报销单 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 油卡登记 | `sc.legacy.fuel.card.fact` | ok | - | - | - |
| 财务中心 | 销项开票申请 | `sc.invoice.registration` | ok | - | - | action_confirm, validate_tier, reject_tier, action_register, action_cancel |
| 财务中心 | 销项开票登记 | `sc.invoice.registration` | ok | - | - | action_confirm, validate_tier, reject_tier, action_register, action_cancel |
| 财务中心 | 往来单位付款 | `sc.payment.execution` | ok | - | - | action_confirm, validate_tier, reject_tier, action_paid, action_cancel |
| 财务中心 | 项目还公司款登记 | `sc.expense.claim` | ok | - | - | action_submit, validate_tier, reject_tier |
| 财务中心 | 充值登记 | `sc.legacy.fuel.card.recharge.fact` | ok | - | - | - |
| 财务中心 | 账户间资金往来 | `sc.fund.account.operation` | ok | - | - | action_confirm, action_done, action_cancel, action_reset_draft |
| 财务中心 | 抵扣登记 | `sc.tax.deduction.registration` | ok | - | - | action_confirm, action_deduct, action_cancel |
| 财务中心 | 自筹垫付收入 | `sc.legacy.self.funding.fact` | ok | - | - | - |
| 财务中心 | 外经证登记 | `sc.legacy.payment.residual.fact` | ok | - | - | - |
| 财务中心 | 自筹保证金 | `tender.guarantee` | ok | - | - | action_confirm, action_cancel, action_reset_draft |
| 财务中心 | 自筹垫付退回 | `sc.legacy.self.funding.fact` | ok | - | - | - |
| 财务中心 | 自筹保证金退回 | `tender.guarantee` | ok | - | - | action_confirm, action_cancel, action_reset_draft |
| 财务中心 | 付款还保证金 | `tender.guarantee` | ok | - | - | action_confirm, action_cancel, action_reset_draft |
| 人事行政 | 请假/休假审批单 | `sc.office.admin.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 人事行政 | 公司人员名册 | `sc.legacy.user.profile` | ok | - | - | - |
| 人事行政 | 项目管理人员工资登记 | `sc.hr.payroll.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 人事行政 | 社保人员登记 | `sc.hr.payroll.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 人事行政 | 社保登记 | `sc.hr.payroll.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 人事行政 | 项目管理人员工资登记 | `sc.hr.payroll.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 人事行政 | 补助 | `sc.hr.payroll.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 资料证照 | 公司资料存档 | `sc.document.admin.document` | ok | - | - | action_submit, action_done, action_cancel, action_reset_draft |
| 基础设置 | 菜单配置 | `ui.menu.config.policy` | ok | - | - | - |
