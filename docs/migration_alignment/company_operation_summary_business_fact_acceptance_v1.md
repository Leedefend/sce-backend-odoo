# Company Operation Summary Business Fact Acceptance v1

Status: `accepted`

Task: `ITER-2026-05-10-COMPANY-OPERATION-SUMMARY`

## Acceptance Principle

The company operation summary is a user-facing continuation report for the
legacy `公司经营情况表`.

The user supplied the expected table shape at:

`/home/odoo/workspace/partner_import_source/公司经营情况表1778418457134.xlsx`

That workbook is a monthly operating statement, not a one-row all-history
company summary. The runtime report must therefore expose one row per month and
carry the same visible business columns before finer procedure-level
reconciliation can be accepted.

## Expected Legacy Layout

The workbook has one sheet and the visible data range is `A1:AF10`.

Primary columns:

| Column | Meaning |
| --- | --- |
| A | 年-月份 |
| B | 营收 |
| C:F | 收入/扣款实缴登记: 管理费, 企业所得税, 增值税附加, 增值税附加(不可退) |
| G:O | 收入/财务收入: 利息公司, 标书制作费, 出场费, 证书费, 公司经营收入, 工会经费, 分公司年费, 残保金, 个人所得税 |
| P | 收入合计 |
| Q | 支出合计 |
| R | 报销申请/报销 |
| S | 工资登记/工资 |
| T:U | 社保登记: 员工社保, 证书社保 |
| V | 扣款实缴退回/增值税附加退项目 |
| W:AF | 公司财务支出: 企业所得税, 个人所得税, 增值税附加交税务局, 投标费, 出场费, 公司经营支出, 利息公司, 残保金, 工会经费, 手续费 |

The workbook rows are `2026年-1月` through `2026年-5月` plus a total row.
`营收` is the displayed operating result: `收入合计 - 支出合计`.

## Runtime Carrier

Acceptance database:

`sc_acceptance_audit_20260510`

Runtime model:

`sc.company.operation.summary`

User entry:

`公司经营情况表`, `action_id=821`, `menu_id=626`

The current projection now uses monthly keys from migrated fact tables and
exposes the workbook-aligned columns above.

## Source Mapping

| Runtime column family | Current migrated fact source |
| --- | --- |
| 扣款实缴登记 | `sc.legacy.account.transaction.line`, `source_table='T_KK_SJDJB_CB'` |
| 财务收入 | `sc.receipt.income`, `legacy_source_table='C_CWSFK_GSCWSR'` |
| 报销申请/报销 | `sc.legacy.expense.reimbursement.line` |
| 工资/员工社保 | `sc.hr.payroll.document` |
| 扣款实缴退回 | `sc.legacy.account.transaction.line`, `source_table='T_KK_SJTHB_CB'` |
| 公司财务支出 | `sc.legacy.account.transaction.line`, `source_table='C_CWSFK_GSCWZC'`, currently classified from available note/category text |

## Current Runtime Evidence

Runtime rows on `sc_acceptance_audit_20260510` after module upgrade:

| 年-月份 | 收入合计 | 支出合计 | 营收 | 管理费 | 企业所得税 | 报销 | 工资 | 增值税附加交税务局 | 来源明细数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026年-1月 | 913433.28 | 1037674.11 | -124240.83 | 201237.88 | 487864.21 | 90969.59 | 431785.64 | 466967.61 | 489 |
| 2026年-2月 | 2727742.74 | 512349.04 | 2215393.70 | 792526.42 | 1359725.07 | 34570.20 | 402309.49 | 40101.84 | 743 |
| 2026年-3月 | 200486.11 | 225368.66 | -24882.55 | 57529.15 | 79748.42 | 42210.00 | 0.00 | 177805.37 | 255 |
| 2026年-4月 | 49953.68 | 6066.40 | 43887.28 | 2699.43 | 18688.86 | 5985.40 | 0.00 | 0.00 | 53 |
| 2026年-5月 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |

## Browser Acceptance

Browser acceptance must verify the user-facing report on daily dev port
`http://localhost:18081` against `sc_acceptance_audit_20260510`.

Required visible checks:

- login user `wutao`
- menu path `统计分析` -> `公司经营情况表`
- visible table title `公司经营情况表`
- visible monthly row such as `2026年-5月`
- visible headers `年-月份`, `营收`, `收入合计`, `支出合计`
- visible workbook-aligned detail headers such as `扣款实缴登记/管理费`,
  `财务收入/标书制作费`, `报销申请/报销`
- amount cells use at most two decimals
- no `未匹配公司` row

Browser evidence:

`artifacts/company-operation-summary-browser-acceptance/20260510T132517/summary.json`

## Residual Interpretation

This iteration corrects the major口径 mistake: the runtime report is now a
monthly operating statement aligned to the user workbook.

Remaining differences should be handled as source-field reconciliation, not by
forcing old data into new concepts. In particular, some old procedure细项 are
not fully structured in the migrated runtime tables yet. For example,
`C_CWSFK_GSCWZC` contains many blank categories, so part of the company expense
classification currently relies on available note text. Certificate social
security and any old procedure-only columns still need source-level extraction
or replay mapping if the user requires exact old-report parity.
