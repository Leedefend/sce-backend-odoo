# 正式办理能力运行矩阵 V1

本矩阵以产品策略中已发布、启用且 `entry_intent=handling` 的正式办理入口为准，检查每个入口是否具备菜单、动作、模型、CRUD 权限、运行态合同和可访问办理 URL。

## 摘要

- 数据库：`sc_demo`
- 正式办理入口：`81`
- 通过入口：`81`
- 失败入口：`0`
- issue 分布：`{}`

## 矩阵

| 中心 | 业务域 | 能力入口 | 模型 | CRUD | 合同 | 运行态字段 | URL | 问题 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 项目中心 |  | 投标报名管理 | `tender.bid` | `RCW` | `tree:Y/form:Y/search:Y` | `list=9 form=69 search=0` | `/a/565?menu_id=476` | PASS |
| 项目中心 |  | 投标报名费申请 | `tender.doc.purchase` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=31 search=0` | `/a/566?menu_id=477` | PASS |
| 合同中心 | 变更签证 | 支出合同签证 | `sc.settlement.adjustment` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=27 search=0` | `/a/674?menu_id=489` | PASS |
| 合同中心 | 变更签证 | 收入合同签证 | `sc.settlement.adjustment` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=27 search=0` | `/a/674?menu_id=484` | PASS |
| 合同中心 | 合同管理 | 一般合同（公司） | `sc.general.contract` | `RCW` | `tree:Y/form:Y/search:Y` | `list=3 form=39 search=0` | `/a/669?menu_id=361` | PASS |
| 合同中心 | 合同管理 | 施工合同 | `construction.contract` | `RCW` | `tree:Y/form:Y/search:Y` | `list=44 form=35 search=0` | `/a/1002?menu_id=389` | PASS |
| 合同中心 | 结算管理 | 支出合同结算 | `sc.settlement.order` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=29 search=0` | `/a/754?menu_id=491` | PASS |
| 合同中心 | 结算管理 | 收入合同结算 | `sc.settlement.order` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=29 search=0` | `/a/753?menu_id=486` | PASS |
| 施工管理 |  | 施工日志 | `sc.construction.diary` | `RCW` | `tree:Y/form:Y/search:Y` | `list=33 form=26 search=0` | `/a/701?menu_id=415` | PASS |
| 施工管理 | 计划进度 | 计划汇报 | `sc.plan.report` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=25 search=0` | `/a/652?menu_id=517` | PASS |
| 施工管理 | 计划进度 | 计划管理 | `sc.plan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=40 search=0` | `/a/651?menu_id=516` | PASS |
| 物资与分包 |  | 材料计划 | `project.material.plan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=16 form=20 search=0` | `/a/525?menu_id=403` | PASS |
| 物资与分包 | 分包管理 | 分包方单 | `sc.subcontract.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=74 search=0` | `/a/967?menu_id=785` | PASS |
| 物资与分包 | 分包管理 | 分包申请 | `sc.subcontract.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=33 form=74 search=0` | `/a/549?menu_id=512` | PASS |
| 物资与分包 | 分包管理 | 分包登记 | `sc.subcontract.register` | `RCW` | `tree:Y/form:Y/search:Y` | `list=33 form=47 search=0` | `/a/550?menu_id=513` | PASS |
| 物资与分包 | 分包管理 | 分包结算 | `sc.subcontract.settlement` | `RCW` | `tree:Y/form:Y/search:Y` | `list=33 form=45 search=0` | `/a/551?menu_id=514` | PASS |
| 物资与分包 | 分包管理 | 分包计划 | `sc.subcontract.plan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=31 search=0` | `/a/548?menu_id=511` | PASS |
| 物资与分包 | 劳务管理 | 劳务申请 | `sc.labor.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=32 form=42 search=0` | `/a/539?menu_id=501` | PASS |
| 物资与分包 | 劳务管理 | 劳务结算 | `sc.labor.settlement` | `RCW` | `tree:Y/form:Y/search:Y` | `list=31 form=41 search=0` | `/a/541?menu_id=503` | PASS |
| 物资与分包 | 劳务管理 | 劳务计划 | `sc.labor.plan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=13 form=25 search=0` | `/a/540?menu_id=500` | PASS |
| 物资与分包 | 劳务管理 | 方单 | `sc.labor.usage` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=67 search=0` | `/a/964?menu_id=779` | PASS |
| 物资与分包 | 劳务管理 | 考勤记录 | `sc.attendance.checkin` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=27 search=0` | `/a/537?menu_id=502` | PASS |
| 物资与分包 | 劳务管理 | 零星用工 | `sc.labor.usage` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=67 search=0` | `/a/965?menu_id=780` | PASS |
| 物资与分包 | 机械管理 | 机械台班记录 | `sc.equipment.usage` | `RCW` | `tree:Y/form:Y/search:Y` | `list=18 form=57 search=0` | `/a/968?menu_id=782` | PASS |
| 物资与分包 | 机械管理 | 设备使用登记 | `sc.equipment.usage` | `RCW` | `tree:Y/form:Y/search:Y` | `list=18 form=57 search=0` | `/a/545?menu_id=506` | PASS |
| 物资与分包 | 机械管理 | 设备申请 | `sc.equipment.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=35 form=44 search=0` | `/a/544?menu_id=505` | PASS |
| 物资与分包 | 机械管理 | 设备结算 | `sc.equipment.settlement` | `RCW` | `tree:Y/form:Y/search:Y` | `list=31 form=40 search=0` | `/a/546?menu_id=507` | PASS |
| 物资与分包 | 机械管理 | 设备计划 | `sc.equipment.plan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=27 search=0` | `/a/543?menu_id=504` | PASS |
| 物资与分包 | 材料管理 | 入库单 | `sc.material.inbound` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=24 search=0` | `/a/988?menu_id=496` | PASS |
| 物资与分包 | 材料管理 | 出库单 | `sc.material.outbound` | `RCW` | `tree:Y/form:Y/search:Y` | `list=19 form=33 search=0` | `/a/530?menu_id=497` | PASS |
| 物资与分包 | 材料管理 | 采购订单 | `purchase.order` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=70 search=0` | `/a/581?menu_id=404` | PASS |
| 物资与分包 | 询价报价 | 报价单 | `sc.material.rfq` | `RCW` | `tree:Y/form:Y/search:Y` | `list=21 form=31 search=0` | `/a/966?menu_id=778` | PASS |
| 财务中心 | 付款管理 | 公司财务支出 | `sc.payment.execution` | `RCW` | `tree:Y/form:Y/search:Y` | `list=8 form=42 search=0` | `/a/779?menu_id=540` | PASS |
| 财务中心 | 付款管理 | 实付登记 | `sc.payment.execution` | `RCW` | `tree:Y/form:Y/search:Y` | `list=19 form=49 search=0` | `/a/806?menu_id=347` | PASS |
| 财务中心 | 付款管理 | 往来单位付款 | `sc.payment.execution` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=42 search=0` | `/a/781?menu_id=551` | PASS |
| 财务中心 | 付款管理 | 支付申请 | `payment.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=37 search=0` | `/a/780?menu_id=786` | PASS |
| 财务中心 | 借还款 | 借款申请 | `sc.financing.loan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=26 form=26 search=0` | `/a/775?menu_id=542` | PASS |
| 财务中心 | 借还款 | 承包人借项目款 | `sc.financing.loan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=12 form=26 search=0` | `/a/776?menu_id=546` | PASS |
| 财务中心 | 借还款 | 承包人还项目款 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=33 search=0` | `/a/768?menu_id=545` | PASS |
| 财务中心 | 借还款 | 还款登记 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=33 search=0` | `/a/767?menu_id=543` | PASS |
| 财务中心 | 借还款 | 项目借公司款登记 | `sc.financing.loan` | `RCW` | `tree:Y/form:Y/search:Y` | `list=17 form=26 search=0` | `/a/777?menu_id=547` | PASS |
| 财务中心 | 借还款 | 项目还公司款登记 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=33 search=0` | `/a/769?menu_id=548` | PASS |
| 财务中心 | 扣款与非现金 | 扣款登记 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=18 form=24 search=0` | `/a/770?menu_id=553` | PASS |
| 财务中心 | 收款管理 | 工程进度款收入登记 | `sc.receipt.income` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=35 search=0` | `/a/949?menu_id=803` | PASS |
| 财务中心 | 收款管理 | 收入 | `sc.receipt.income` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=35 search=0` | `/a/778?menu_id=539` | PASS |
| 财务中心 | 收款管理 | 收款申请 | `payment.request` | `RCW` | `tree:Y/form:Y/search:Y` | `list=51 form=37 search=0` | `/a/672?menu_id=363` | PASS |
| 财务中心 | 收款管理 | 收款登记 | `sc.receipt.income` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=72 search=0` | `/a/628?menu_id=346` | PASS |
| 财务中心 | 结算管理 | 结算单 | `sc.settlement.order` | `RCW` | `tree:Y/form:Y/search:Y` | `list=19 form=87 search=0` | `/a/675?menu_id=365` | PASS |
| 财务中心 | 结算管理 | 结算调整 | `sc.settlement.adjustment` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=27 search=0` | `/a/674?menu_id=366` | PASS |
| 财务中心 | 自筹资金 | 自筹垫付收入 | `sc.self.funding.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=13 form=29 search=0` | `/a/998?menu_id=731` | PASS |
| 财务中心 | 自筹资金 | 自筹退回 | `sc.self.funding.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=13 form=29 search=0` | `/a/999?menu_id=732` | PASS |
| 财务中心 | 账户资金 | 账户间资金往来 | `sc.fund.account.operation` | `RCW` | `tree:Y/form:Y/search:Y` | `list=23 form=24 search=0` | `/a/782?menu_id=557` | PASS |
| 财务中心 | 账户资金 | 资金对账 | `sc.treasury.reconciliation` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=32 search=0` | `/a/627?menu_id=345` | PASS |
| 财务中心 | 费用 | 付款还保证金 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=10 form=16 search=0` | `/a/814?menu_id=615` | PASS |
| 财务中心 | 费用 | 付款还保证金退回 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=10 form=16 search=0` | `/a/1010?menu_id=806` | PASS |
| 财务中心 | 费用 | 报销申请 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/764?menu_id=568` | PASS |
| 财务中心 | 费用 | 项目费用报销单 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/773?menu_id=569` | PASS |
| 财务中心 | 费用与保证金 | 付款保证金退回 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=69 search=0` | `/a/815?menu_id=616` | PASS |
| 财务中心 | 费用与保证金 | 合同保证金支付 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/985?menu_id=573` | PASS |
| 财务中心 | 费用与保证金 | 合同保证金退回 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/986?menu_id=574` | PASS |
| 财务中心 | 费用与保证金 | 扣款实缴登记 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=33 search=0` | `/a/771?menu_id=554` | PASS |
| 财务中心 | 费用与保证金 | 扣款实缴退回 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=33 search=0` | `/a/772?menu_id=555` | PASS |
| 财务中心 | 费用与保证金 | 投标保证金支付 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/983?menu_id=571` | PASS |
| 财务中心 | 费用与保证金 | 投标保证金退回 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=33 search=0` | `/a/984?menu_id=572` | PASS |
| 财务中心 | 费用与保证金 | 费用报销单 | `sc.expense.claim` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=69 search=0` | `/a/763?menu_id=344` | PASS |
| 人事行政 |  | 社保人员登记 | `sc.hr.payroll.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=16 form=78 search=0` | `/a/644?menu_id=353` | PASS |
| 人事行政 |  | 社保登记 | `sc.hr.payroll.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=78 search=0` | `/a/645?menu_id=354` | PASS |
| 人事行政 |  | 补助 | `sc.hr.payroll.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=13 form=78 search=0` | `/a/646?menu_id=356` | PASS |
| 人事行政 |  | 项目管理人员工资登记 | `sc.hr.payroll.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=18 form=94 search=0` | `/a/862?menu_id=805` | PASS |
| 人事行政 | 薪资福利 | 奖金 | `sc.hr.payroll.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=10 form=78 search=0` | `/a/648?menu_id=357` | PASS |
| 人事行政 | 行政审批 | 印章使用审批表 | `sc.office.admin.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=23 form=92 search=0` | `/a/643?menu_id=352` | PASS |
| 人事行政 | 请假 | 请假/休假审批单 | `sc.office.admin.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=15 form=92 search=0` | `/a/642?menu_id=351` | PASS |
| 资料证照 |  | 公司资料存档 | `sc.document.admin.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=9 form=70 search=0` | `/a/615?menu_id=337` | PASS |
| 资料证照 | 证照管理 | 证照登记 | `sc.document.admin.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=9 form=70 search=0` | `/a/649?menu_id=359` | PASS |
| 资料证照 | 资料借阅 | 借阅申请 | `sc.document.admin.document` | `RCW` | `tree:Y/form:Y/search:Y` | `list=28 form=70 search=0` | `/a/650?menu_id=360` | PASS |
| 税务中心 |  | 外经证登记 | `sc.legacy.payment.residual.fact` | `RCW` | `tree:Y/form:Y/search:Y` | `list=20 form=50 search=0` | `/a/762?menu_id=533` | PASS |
| 税务中心 |  | 抵扣登记 | `sc.tax.deduction.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=14 form=35 search=0` | `/a/761?menu_id=532` | PASS |
| 税务中心 |  | 进项发票 | `sc.invoice.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=19 form=71 search=0` | `/a/756?menu_id=526` | PASS |
| 税务中心 |  | 销项开票申请 | `sc.invoice.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=26 form=39 search=0` | `/a/757?menu_id=528` | PASS |
| 税务中心 |  | 销项开票登记 | `sc.invoice.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=18 form=42 search=0` | `/a/758?menu_id=529` | PASS |
| 税务中心 |  | 预缴税款 | `sc.invoice.registration` | `RCW` | `tree:Y/form:Y/search:Y` | `list=69 form=37 search=0` | `/a/759?menu_id=530` | PASS |
