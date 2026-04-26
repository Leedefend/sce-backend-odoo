# Legacy Remaining Value Analysis v1

Date: 2026-04-26

This pass screens restored `LegacyDb` content after the production-sim history
replay. It focuses on facts that still have business value for a fresh-system
cutover, while keeping old facts separate from new workflow and permission
semantics.

## Current Target Coverage Snapshot

`sc_prod_sim` after the latest replay:

| Target fact | Count |
| --- | ---: |
| historical users (`login like legacy_%`) | 101 |
| `sc.legacy.user.profile` | 101 |
| `sc.legacy.department` | 828 |
| `sc.legacy.user.role` | 330 |
| `sc.legacy.user.project.scope` | 90871 |
| `sc.legacy.task.evidence` | 78822 |
| `sc.legacy.attendance.checkin` | 106208 |
| `sc.legacy.personnel.movement` | 20804 |
| `sc.project.member.staging` | 15155 |
| `sc.legacy.workflow.audit` | 79702 |
| `sc.legacy.invoice.tax.fact` | 5920 |
| `sc.legacy.invoice.registration.line` | 25393 |
| `sc.legacy.deduction.adjustment.line` | 13521 |
| `sc.legacy.fund.confirmation.line` | 13398 |
| `sc.legacy.expense.reimbursement.line` | 3589 |
| `sc.legacy.construction.diary.line` | 5687 |
| `sc.legacy.payment.residual.fact` | 1846 |
| `sc.legacy.receipt.residual.fact` | 4357 |
| `sc.legacy.receipt.income.fact` | 7220 |
| `sc.legacy.expense.deposit.fact` | 11167 |
| `sc.legacy.financing.loan.fact` | 318 |
| `sc.legacy.fund.daily.snapshot.fact` | 496 |
| `sc.legacy.material.category` | 130624 |
| `sc.legacy.material.detail` | 2279734 |
| `sc.legacy.file.index` | 178931 |
| `ir.attachment` | 19546 |
| `product.template` | 1 |
| `product.product` | 1 |

## High-Value Remaining Candidates

| Priority | Lane | Source tables | Source scale | Current conclusion |
| --- | --- | --- | ---: | --- |
| P0 | material catalog search archive | `T_Base_MaterialDetail`, `T_Base_BuildMaterialClass`, `C_Base_CBFL` | 2,279,734 material rows; 16 global material categories; 3 orphan category keys; 130,605 cost category rows | Covered by neutral archive. Do not load as products; preserve as searchable historical material/category facts. |
| P0 | attachment index expansion | `BASE_SYSTEM_FILE`, `T_BILL_FILE` | 126,967 + 51,964 rows; about 124.6 GB referenced size | Covered by neutral file index. Binary transfer remains a separate file-custody decision. |
| P1 | task / todo evidence | `T_BASE_TASKDONE` | 78,822 rows | Covered by neutral evidence archive. Kept as historical read/done evidence, not new activities. |
| P1 | user project scope evidence | `T_System_UserAndXXGL`, `T_System_UserAndXXGL_History` | 20,000 current + 70,871 history rows | Covered by neutral scope evidence. Does not grant new-system visibility. |
| P1 | special invoice registration | `C_JXXP_ZYFPJJD`, `C_JXXP_ZYFPJJD_CB` | 16,616 headers; 25,393 lines; line total about 2.28B | Covered by neutral line-level invoice registration archive. Keeps old invoice facts separate from new-system invoice rules. |
| P1 | deduction / settlement adjustment | `T_KK_SJDJB`, `T_KK_SJDJB_CB` | 2,636 headers; 13,521 lines; current line sum about 264.8M | Covered by neutral deduction/settlement adjustment archive. Not promoted to native settlement state. |
| P1 | fund confirmation detail | `ZJGL_SZQR_DKQRB`, `ZJGL_SZQR_DKQRB_CB` | 2,655 headers; 13,398 lines; current line sum about 260.8M | Covered by neutral fund confirmation archive. Does not update native fund/receipt states. |
| P1 | expense reimbursement detail | `CWGL_FYBX`, `CWGL_FYBX_CB` | 1,866 headers; 3,589 lines; line total about 11.89M | Covered by neutral reimbursement line archive. Not promoted to native reimbursement approval, payment, or accounting state. |
| P1 | construction diary / quality notes | `SGZL_RZRJ`, `SGZL_RZRJ_CB` | 4,340 headers; 5,687 lines | Covered by neutral construction diary archive. Keeps project field facts without changing new task, quality, or document workflow state. |
| P1 | payment runtime residuals | `C_ZFSQGL`, `T_FK_Supplier` | 1,362 outflow request residuals; 484 actual outflow residuals | Covered by neutral payment residual archive. These rows are not promoted to `payment.request`, ledger, settlement, or accounting state. |
| P1 | receipt runtime residuals | `C_JFHKLR` | 4,357 receipt residuals | Covered by neutral receipt residual archive. These rows are not promoted to receive requests, treasury ledger, settlement, or invoice state. |
| P2 | attendance / check-in | `CheckInData` | 106,208 rows; 88 users; 13,932 active-like; 2019-2023 | Covered by privacy-restricted neutral archive. Not new attendance, approval, payroll, or permission state. |
| P2 | personnel movement | `PM_RYYDGL` | 20,804 rows | Covered by privacy-restricted neutral archive. Not new employee, permission, payroll, or org state. |
| P2 | salary lines | `BGGL_XZ_GZ_CB` | 3,458 rows; 111 people; total about 30.56M | Highly sensitive. Only migrate if explicitly required; encrypted/restricted neutral carrier. |
| P3 | low-code edit history | `BASE_LOWCODE_HISTORYDATA` | 97,037 rows across 9 configs; most `CONFIGID` null | Mostly platform audit/config history. Lower business value unless needed for legal traceability. |

## Supporting Source Metrics

Material archive:

- `T_Base_MaterialDetail`: 2,279,734 rows, 2,279,732 active-like, 255
  distinct project refs, 2,279,708 named, 693,590 with unit, only 25 priced.
- `T_Base_BuildMaterialClass`: 16 global category rows referenced by material
  details.
- `T_Base_MaterialDetail`: 3 category GUIDs are referenced by 1,512 detail
  rows but missing from the category master; these are preserved as explicit
  orphan-category carrier rows.
- `C_Base_CBFL`: 130,605 rows, 130,584 active-like, 476 distinct project refs.

Attachments:

- `BASE_SYSTEM_FILE`: 126,967 rows, 125,213 active-like, about 84.2 GB.
- `T_BILL_FILE`: 51,964 rows, 49,148 active-like, about 40.4 GB.
- `sc.legacy.file.index`: 178,931 neutral index rows after replay; this is the
  union of both source tables and does not copy binary content into Odoo.
- Common `BASE_SYSTEM_FILE` extensions: `png` 42,560, `pdf` 40,042,
  `jpg` 36,678.
- Top `T_BILL_FILE.BillType`: `PaymentApply` 15,163, `ZJSWGL`
  12,061, `BGGL` 4,753, `BuildingProperty` 2,836,
  `SupplierContracts` 2,565.

Financial/detail candidates:

- `C_JXXP_ZYFPJJD_CB`: 25,393 rows, all with invoice number, total amount
  about 2,282,867,004.11, tax about 115,434,418.08.
- `T_KK_SJDJB_CB`: 13,521 rows, current amount about 264,765,389.58.
- `ZJGL_SZQR_DKQRB_CB`: 13,398 rows, current amount about 260,848,353.69.
- `CWGL_FYBX_CB`: 3,589 rows, line amount about 11,888,847.96; header
  approved amount about 11,869,461.66.
- `SGZL_RZRJ_CB`: 5,687 rows under 4,340 construction diary headers; preserves
  diary descriptions, quality/detail text, and attachment path references.

## Recommended Next Move

1. Decide binary transfer policy by file type, legal retention, storage
   availability, and business object coverage.
2. Review the remaining payment/outflow residual rows against current
   `payment.request` runtime coverage.
3. Treat attendance, personnel movement, and salary as opt-in privacy lanes,
   behind explicit authorization and restricted ACLs.
