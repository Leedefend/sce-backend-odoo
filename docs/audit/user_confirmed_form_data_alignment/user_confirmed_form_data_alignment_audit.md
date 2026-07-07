# 用户确认菜单表单数据对齐审计

- 产品：`construction.standard`
- 菜单数：62
- 总记录数：260357
- 已检查记录数：2858
- 已检查正式字段：801
- 数据不一致菜单：0
- 仍需正式字段承接菜单：0

| 分组 | 菜单 | 模型 | 记录 | 严重度 | 不一致字段 | 只读历史来源字段 |
| --- | --- | --- | ---: | --- | --- | --- |
| 基础资料 | 客户 | `res.partner` | 1139 | ok | - | - |
| 基础资料 | 供应商 | `res.partner` | 6321 | ok | - | - |
| 项目中心 | 项目台账 | `project.project` | 923 | ok | - | - |
| 项目中心 | 投标报名管理 | `tender.bid` | 2886 | ok | - | - |
| 项目中心 | 投标报名费申请 | `tender.doc.purchase` | 125 | ok | - | - |
| 合同中心 | 一般合同（公司） | `sc.general.contract` | 45 | ok | - | - |
| 合同中心 | 补充合同 | `construction.contract.expense` | 2 | ok | - | - |
| 合同中心 | 收入合同执行 | `construction.contract.income` | 1711 | ok | - | - |
| 合同中心 | 支出合同执行 | `construction.contract.expense` | 8387 | ok | - | - |
| 合同中心 | 收入合同结算 | `sc.settlement.order` | 37 | ok | - | - |
| 合同中心 | 支出合同结算 | `sc.settlement.order` | 3225 | ok | - | - |
| 施工管理 | 施工日志 | `sc.construction.diary` | 3233 | ok | - | - |
| 物资与分包 | 材料计划 | `project.material.plan` | 686 | ok | - | - |
| 物资与分包 | 租入 | `sc.legacy.direct.acceptance.fact` | 166 | ok | - | - |
| 物资与分包 | 分包方单 | `sc.subcontract.request` | 721 | ok | - | - |
| 物资与分包 | 还租 | `sc.legacy.direct.acceptance.fact` | 37 | ok | - | - |
| 物资与分包 | 方单 | `sc.labor.usage` | 252 | ok | - | - |
| 物资与分包 | 机械台班记录 | `sc.equipment.usage` | 17502 | ok | - | - |
| 物资与分包 | 零星用工 | `sc.labor.usage` | 8794 | ok | - | - |
| 物资与分包 | 报价单 | `sc.material.rfq` | 126 | ok | - | - |
| 物资与分包 | 入库单 | `sc.material.inbound` | 13184 | ok | - | - |
| 物资与分包 | 出库单 | `sc.material.outbound` | 3 | ok | - | - |
| 财务中心 | 收入 | `sc.receipt.income` | 29638 | ok | - | - |
| 财务中心 | 承包人还项目款 | `sc.expense.claim` | 425 | ok | - | - |
| 财务中心 | 扣款单 | `sc.tax.deduction.registration` | 136 | ok | - | - |
| 财务中心 | 到款确认表 | `sc.legacy.fund.confirmation.document` | 5205 | ok | - | - |
| 财务中心 | 资金日报表 | `sc.fund.account.operation` | 7453 | ok | - | - |
| 财务中心 | 报销申请 | `sc.expense.claim` | 3583 | ok | - | - |
| 财务中心 | 工程进度款收入登记 | `sc.receipt.income` | 639 | ok | - | - |
| 财务中心 | 付款还保证金退回 | `tender.guarantee` | 1909 | ok | - | - |
| 财务中心 | 公司财务支出 | `sc.expense.claim` | 2727 | ok | - | - |
| 财务中心 | 承包人借项目款 | `sc.financing.loan` | 227 | ok | - | - |
| 财务中心 | 扣款实缴登记 | `sc.expense.claim` | 13264 | ok | - | - |
| 财务中心 | 支付申请 | `payment.request` | 2598 | ok | - | - |
| 财务中心 | 进项发票 | `sc.invoice.registration` | 52545 | ok | - | - |
| 财务中心 | 预缴税款 | `sc.invoice.registration` | 12716 | ok | - | - |
| 财务中心 | 项目借公司款登记 | `sc.financing.loan` | 872 | ok | - | - |
| 财务中心 | 扣款实缴退回 | `sc.expense.claim` | 1800 | ok | - | - |
| 财务中心 | 项目费用报销单 | `sc.expense.claim` | 5806 | ok | - | - |
| 财务中心 | 油卡登记 | `sc.legacy.fuel.card.fact` | 8 | ok | - | - |
| 财务中心 | 销项开票申请 | `sc.invoice.registration` | 221 | ok | - | - |
| 财务中心 | 销项开票登记 | `sc.invoice.registration` | 383 | ok | - | - |
| 财务中心 | 往来单位付款 | `sc.payment.execution` | 10359 | ok | - | - |
| 财务中心 | 项目还公司款登记 | `sc.expense.claim` | 5 | ok | - | - |
| 财务中心 | 充值登记 | `sc.legacy.fuel.card.recharge.fact` | 32 | ok | - | - |
| 财务中心 | 账户间资金往来 | `sc.fund.account.operation` | 395 | ok | - | - |
| 财务中心 | 抵扣登记 | `sc.tax.deduction.registration` | 5043 | ok | - | - |
| 财务中心 | 自筹垫付收入 | `sc.legacy.self.funding.fact` | 2144 | ok | - | - |
| 财务中心 | 外经证登记 | `sc.legacy.payment.residual.fact` | 318 | ok | - | - |
| 财务中心 | 自筹保证金 | `tender.guarantee` | 1581 | ok | - | - |
| 财务中心 | 自筹垫付退回 | `sc.legacy.self.funding.fact` | 827 | ok | - | - |
| 财务中心 | 自筹保证金退回 | `tender.guarantee` | 823 | ok | - | - |
| 财务中心 | 付款还保证金 | `tender.guarantee` | 2943 | ok | - | - |
| 人事行政 | 请假/休假审批单 | `sc.office.admin.document` | 686 | ok | - | - |
| 人事行政 | 公司人员名册 | `sc.legacy.user.profile` | 39 | ok | - | - |
| 人事行政 | 项目管理人员工资登记 | `sc.hr.payroll.document` | 3398 | ok | - | - |
| 人事行政 | 社保人员登记 | `sc.hr.payroll.document` | 329 | ok | - | - |
| 人事行政 | 社保登记 | `sc.hr.payroll.document` | 3546 | ok | - | - |
| 人事行政 | 项目管理人员工资登记 | `sc.hr.payroll.document` | 233 | ok | - | - |
| 人事行政 | 补助 | `sc.hr.payroll.document` | 229 | ok | - | - |
| 资料证照 | 公司资料存档 | `sc.document.admin.document` | 14997 | ok | - | - |
| 基础设置 | 菜单配置 | `ui.menu.config.policy` | 770 | ok | - | - |

## 差异示例
