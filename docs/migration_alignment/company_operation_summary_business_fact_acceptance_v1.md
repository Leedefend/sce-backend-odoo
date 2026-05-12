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
| 公司财务支出 | `sc.legacy.account.transaction.line`, `source_table='C_CWSFK_GSCWZC'`, classified from structured `D_SCBSJS_CWZCLB`/category |

## Fact Supplement Replay

This iteration supplements deterministic legacy facts before further business
ability upgrades:

| Fact family | Result |
| --- | ---: |
| `BGGL_XZ_JXDJ_ZB` + `BGGL_XZ_JXDJ` social registration payload rows | 2523 |
| social registration rows replayed into `sc.hr.payroll.document` | 2517 |
| active social registration rows | 1908 |
| 2026 active social registration amount, 个人挂靠 | 143881.76 |
| 2026 active social registration amount, 员工 | 229979.04 |
| 2026 active social registration amount, 证书挂靠 | 12839.52 |
| account transaction payload rows after refund fact recovery | 41384 |
| existing account transaction rows refreshed | 39707 |
| `T_KK_SJTHB_CB` refund rows newly replayed | 1677 |
| replayed refund rows with missing old account fields | 1677 |

The `T_KK_SJTHB_CB` legacy refund headers frequently have empty `KKZH/KKZHID`.
Those rows are still objective business facts, so the replay now keeps them and
marks account resolution as missing instead of dropping the refund facts.

## Current Runtime Evidence

Runtime rows on `sc_acceptance_audit_20260510` after module upgrade:

| 年-月份 | 收入合计 | 支出合计 | 营收 | 管理费 | 企业所得税 | 报销 | 工资 | 增值税附加交税务局 | 来源明细数 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026年-1月 | 897752.10 | 405466.28 | 492285.82 | 185556.70 | 487864.21 | 90969.59 | 115949.19 | 50032.25 | 494 |
| 2026年-2月 | 2289686.53 | 416919.35 | 1872767.18 | 354470.21 | 1359725.07 | 34570.20 | 114970.81 | 40101.84 | 760 |
| 2026年-3月 | 172998.23 | 414230.55 | -241232.32 | 30041.27 | 79748.42 | 42210.00 | 0.00 | 177805.37 | 261 |
| 2026年-4月 | 49953.68 | 5986.40 | 43967.28 | 2699.43 | 18688.86 | 5985.40 | 0.00 | 0.00 | 56 |
| 2026年-5月 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0 |

Supplemented runtime evidence:

| 年-月份 | 员工社保 | 证书社保 | 扣款实缴退回/增值税附加退项目 |
| --- | ---: | ---: | ---: |
| 2026年-1月 | 77734.80 | 3204.72 | 24085.58 |
| 2026年-2月 | 77734.80 | 3204.72 | 142951.41 |
| 2026年-3月 | 74509.44 | 6430.08 | 108191.06 |
| 2026年-4月 | 0.00 | 0.00 | 0.00 |
| 2026年-5月 | 0.00 | 0.00 | 0.00 |

## Source Audit

Audit command:

`python3 scripts/verify/company_operation_summary_source_audit.py`

Current artifact:

`artifacts/company-operation-summary-source-audit/20260510T215620/summary.json`

The audit compares three surfaces:

- user workbook: `/home/odoo/workspace/partner_import_source/公司经营情况表1778418457134.xlsx`
- restored legacy procedure: `Report_GSJYQKB_BSJZ`, year `2026`, empty start/end date
- runtime projection: `sc_company_operation_summary` on `sc_acceptance_audit_20260510`

Current result:

| Check | Result |
| --- | ---: |
| compared periods | 5 |
| compared columns | 31 |
| Excel vs runtime mismatches | 34 |
| full mismatch records including restored proc | 111 |

Corrections already made from this audit:

- `扣款实缴登记/管理费` now excludes returned rows by using
  `sc.legacy.deduction.adjustment.line.returned_flag = '否'`.
- `工资登记/工资` now uses the company-side salary rows instead of mixing in
  project-department wages.
- `公司财务支出/增值税附加交税务局` no longer double-counts the VAT principal
  row when the same note also contains surcharge components.
- `社保登记/员工社保` and `社保登记/证书社保` now use replayed
  `BGGL_XZ_JXDJ*` facts and split `员工` from `证书挂靠`.
- `扣款实缴退回/增值税附加退项目` now uses replayed `T_KK_SJTHB_CB`
  refund facts, including old rows whose refund header has no account field.
- `公司财务支出` subcolumns now use the structured old category field
  `D_SCBSJS_CWZCLB` where available instead of note-text guessing.

Remaining audit conclusions:

- January and February now have zero Excel-vs-runtime differences in the
  audited user workbook columns.
- March still differs on `工资登记/工资`: the workbook has `114182.16`, while
  runtime has no company-side salary fact for March in the currently restored
  source snapshot.
- April and May still differ because the supplied workbook contains later
  business facts that are not present in the currently restored legacy DB
  snapshot for several source families. This is a source-snapshot gap, not a
  reason to invent values in the runtime projection.
- The restored legacy procedure `Report_GSJYQKB_BSJZ` still differs from both
  the workbook and runtime in many columns, indicating that the procedure is not
  a reliable single authority for this workbook export without further source
  date/snapshot alignment.

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

`artifacts/company-operation-summary-browser-acceptance/20260510T135638/summary.json`

## Residual Interpretation

This iteration corrects the major口径 mistake: the runtime report is now a
monthly operating statement aligned to the user workbook.

Remaining differences should be handled as source-snapshot and source-field
reconciliation, not by forcing old data into new concepts. The next
reconciliation step should refresh the audit DB from a source snapshot that
contains the workbook's later March, April, and May 2026 facts before declaring
full numeric parity.
