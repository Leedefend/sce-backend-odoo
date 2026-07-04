# SCBS55 Runtime List Strict Probe v1

Status: PASS
Database: sc_odoo
Generated At: 2026-05-28T22:43:38.816829+00:00

| seq | menu | model | expected | runtime | extra | missing | record extra | status |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 10 | 供应商/合作单位 | sc.business.entity | 12 | 12 | 0 | 0 | 0 | PASS |
| 20 | 往来单位 | sc.business.entity | 11 | 11 | 0 | 0 | 0 | PASS |
| 30 | 施工合同 | construction.contract | 21 | 21 | 0 | 0 | 0 | PASS |
| 40 | 公司资料存档 | sc.document.admin.document | 7 | 7 | 0 | 0 | 0 | PASS |
| 50 | 请假/休假审批单 | sc.office.admin.document | 13 | 13 | 0 | 0 | 0 | PASS |
| 60 | 印章使用审批表 | sc.office.admin.document | 21 | 21 | 0 | 0 | 0 | PASS |
| 70 | 组织机构 | hr.department | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 80 | 公司人员名册（配置） | sc.legacy.user.profile | 28 | 27 | 0 | 0 | 0 | PASS |
| 90 | 社保人员登记 | sc.hr.payroll.document | 14 | 14 | 0 | 0 | 0 | PASS |
| 100 | 社保登记 | sc.hr.payroll.document | 13 | 13 | 0 | 0 | 0 | PASS |
| 110 | 工资登记 | sc.hr.payroll.document | 16 | 16 | 0 | 0 | 0 | PASS |
| 120 | 补助 | sc.hr.payroll.document | 11 | 11 | 0 | 0 | 0 | PASS |
| 130 | 奖金 | sc.hr.payroll.document | 8 | 8 | 0 | 0 | 0 | PASS |
| 140 | 证照登记 | sc.document.admin.document | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 150 | 借阅申请 | sc.document.admin.document | 26 | 26 | 0 | 0 | 0 | PASS |
| 160 | 投标报名管理 | tender.bid | 7 | 7 | 0 | 0 | 0 | PASS |
| 170 | 投标报名费申请 | tender.doc.purchase | 14 | 14 | 0 | 0 | 0 | PASS |
| 180 | 自筹保证金 | tender.guarantee | 16 | 16 | 0 | 0 | 0 | PASS |
| 190 | 自筹保证金退回 | tender.guarantee | 15 | 15 | 0 | 0 | 0 | PASS |
| 200 | 付款还保证金 | tender.guarantee | 18 | 18 | 0 | 0 | 0 | PASS |
| 210 | 付款还保证金退回 | tender.guarantee | 14 | 14 | 0 | 0 | 0 | PASS |
| 220 | 借款申请 | sc.financing.loan | 26 | 26 | 0 | 0 | 0 | PASS |
| 230 | 还款登记 | sc.financing.loan | 12 | 12 | 0 | 0 | 0 | PASS |
| 240 | 报销申请 | sc.expense.claim | 13 | 13 | 0 | 0 | 0 | PASS |
| 250 | 收入 | sc.receipt.income | 12 | 12 | 0 | 0 | 0 | PASS |
| 260 | 公司财务支出 | sc.expense.claim | 12 | 12 | 0 | 0 | 0 | PASS |
| 270 | 承包人还项目款 | sc.expense.claim | 14 | 14 | 0 | 0 | 0 | PASS |
| 280 | 承包人借项目款 | sc.financing.loan | 12 | 12 | 0 | 0 | 0 | PASS |
| 290 | 支付申请 | payment.request | 19 | 19 | 0 | 0 | 0 | PASS |
| 300 | 扣款单 | sc.tax.deduction.registration | 10 | 10 | 0 | 0 | 0 | PASS |
| 310 | 往来单位付款 | sc.payment.execution | 18 | 18 | 0 | 0 | 0 | PASS |
| 320 | 账户间资金往来 | sc.fund.account.operation | 13 | 13 | 0 | 0 | 0 | PASS |
| 330 | 扣款实缴登记 | sc.expense.claim | 11 | 11 | 0 | 0 | 0 | PASS |
| 340 | 扣款实缴退回 | sc.expense.claim | 10 | 10 | 0 | 0 | 0 | PASS |
| 350 | 到款确认表 | sc.legacy.fund.confirmation.document | 16 | 16 | 0 | 0 | 0 | PASS |
| 360 | 资金日报表 | sc.legacy.fund.daily.line | 14 | 14 | 0 | 0 | 0 | PASS |
| 370 | 项目借公司款登记 | sc.financing.loan | 17 | 17 | 0 | 0 | 0 | PASS |
| 380 | 项目还公司款登记 | sc.financing.loan | 15 | 15 | 0 | 0 | 0 | PASS |
| 390 | 开票申请 | sc.invoice.registration | 17 | 17 | 0 | 0 | 0 | PASS |
| 400 | 开票登记 | sc.invoice.registration | 20 | 20 | 0 | 0 | 0 | PASS |
| 410 | 预缴税款 | sc.invoice.registration | 14 | 14 | 0 | 0 | 0 | PASS |
| 420 | 进项上报 | sc.legacy.invoice.tax.fact | 18 | 18 | 0 | 0 | 0 | PASS |
| 430 | 抵扣登记 | sc.tax.deduction.registration | 12 | 12 | 0 | 0 | 0 | PASS |
| 440 | 外经证登记 | sc.legacy.payment.residual.fact | 20 | 20 | 0 | 0 | 0 | PASS |
| 450 | 供货合同分析 | sc.legacy.supplier.contract.pricing.fact | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 460 | 库存统计表（新） | sc.material.stock.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 470 | 账户收支统计表 | sc.account.income.expense.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 480 | 成本统计表（综合） | sc.comprehensive.cost.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 490 | 投标保证金报表 | sc.tender.guarantee.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 500 | 发票成本进度报表 | sc.invoice.cost.progress.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 510 | 发票分析报表 | sc.invoice.analysis.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 520 | 项目经营统计表 | sc.project.operation.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 530 | 应收应付报表 | sc.ar.ap.report.summary | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 540 | 成本大屏 | sc.dashboard.cockpit.fact | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |
| 550 | 经营大屏 | sc.operating.metrics.project | 0 | 0 | 0 | 0 | 0 | SKIP_NO_LIST_CONTRACT |

## Failures

```json
[]
```
