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
| 扣款实缴登记 | `sc.legacy.deduction.adjustment.line`, `source_table='T_KK_SJDJB_CB'` |
| 财务收入 | `sc.receipt.income`, `legacy_source_table='C_CWSFK_GSCWSR'` |
| 报销申请/报销 | `sc.legacy.expense.reimbursement.line` |
| 工资/员工社保 | `sc.hr.payroll.document` |
| 扣款实缴退回 | `sc.legacy.account.transaction.line`, `source_table='T_KK_SJTHB_CB'` |
| 公司财务支出 | `sc.legacy.account.transaction.line`, `source_table='C_CWSFK_GSCWZC'`, currently classified from available note/category text |

## Current Runtime Evidence

Runtime rows on `sc_acceptance_audit_20260510` after module upgrade:

| 年-月份 | 收入合计 | 支出合计 | 营收 | 管理费 | 企业所得税 | 报销 | 工资 | 增值税附加交税务局 | 来源明细数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026年-1月 | 897752.10 | 304902.30 | 592849.80 | 185556.70 | 487864.21 | 90969.59 | 115949.19 | 50032.25 | 494 |
| 2026年-2月 | 2289686.53 | 225010.36 | 2064676.17 | 354470.21 | 1359725.07 | 34570.20 | 114970.81 | 40101.84 | 760 |
| 2026年-3月 | 172998.23 | 225368.66 | -52370.43 | 30041.27 | 79748.42 | 42210.00 | 0.00 | 177805.37 | 261 |
| 2026年-4月 | 49953.68 | 6066.40 | 43887.28 | 2699.43 | 18688.86 | 5985.40 | 0.00 | 0.00 | 56 |
| 2026年-5月 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |

## Source Audit

Audit command:

`python3 scripts/verify/company_operation_summary_source_audit.py`

Current artifact:

`artifacts/company-operation-summary-source-audit/20260510T214107/summary.json`

The audit compares three surfaces:

- user workbook: `/home/odoo/workspace/partner_import_source/公司经营情况表1778418457134.xlsx`
- restored legacy procedure: `Report_GSJYQKB_BSJZ`, year `2026`, empty start/end date
- runtime projection: `sc_company_operation_summary` on `sc_acceptance_audit_20260510`

Current result:

| Check | Result |
| --- | ---: |
| compared periods | 5 |
| compared columns | 31 |
| Excel vs runtime mismatches | 55 |
| full mismatch records including restored proc | 114 |

Corrections already made from this audit:

- `扣款实缴登记/管理费` now excludes returned rows by using
  `sc.legacy.deduction.adjustment.line.returned_flag = '否'`.
- `工资登记/工资` now uses the company-side salary rows instead of mixing in
  project-department wages.
- `公司财务支出/增值税附加交税务局` no longer double-counts the VAT principal
  row when the same note also contains surcharge components.

Remaining audit conclusions:

- `社保登记/员工社保` and `社保登记/证书社保` are not fully aligned because the
  workbook/procedure source is `BGGL_XZ_JXDJ_ZB` + `BGGL_XZ_JXDJ`, while the
  audit database does not currently carry those rows as structured runtime
  facts.
- `扣款实缴退回/增值税附加退项目` is not aligned because `T_KK_SJTHB_CB` refund
  rows are not present in `sc.legacy.account.transaction.line` on the audit DB.
- Several `公司财务支出` subcolumns still rely on available note text because
  the old source field `D_SCBSJS_CWZCLB` was not preserved as a structured
  category in the current account transaction replay.
- The supplied workbook has non-zero May 2026 data, but the restored legacy DB
  and current audit DB both have zero May rows for the queried source families.
  This indicates the audit DB/legacy restore snapshot is older or incomplete
  relative to the workbook export, so May cannot be reconciled from the current
  available facts.

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

`artifacts/company-operation-summary-browser-acceptance/20260510T134107/summary.json`

## Residual Interpretation

This iteration corrects the major口径 mistake: the runtime report is now a
monthly operating statement aligned to the user workbook.

Remaining differences should be handled as source-field reconciliation, not by
forcing old data into new concepts. The next replay/projection iteration should
preserve `D_SCBSJS_CWZCLB`, load `BGGL_XZ_JXDJ*`, load `T_KK_SJTHB_CB`, and
refresh the audit DB from a source snapshot that contains the workbook's May
2026 facts before declaring full numeric parity.
