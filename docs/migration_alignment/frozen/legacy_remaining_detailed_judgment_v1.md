# Legacy Remaining Detailed Judgment v1

Status: `PASS`

This report gives a detailed business-level judgment for remaining old-system data after the current 23-package asset bus.

## Coverage Baseline

- raw workflow rows: `163245`
- covered rows: `118236`
- remaining rows: `45009`
- DB writes: `0`
- Odoo shell: `false`

## Detailed Decision Matrix

| Family | Rows | Layer | Decision | Next action |
|---|---:|---|---|---|
| payment_request_residual | 5948 | core_business_fact_candidate | no_further_assetization | none |
| supplier_or_purchase_residual | 2607 | mixed_master_and_business_fact | screen_only_for_T_CGHT_INFO_then_decide | open read-only screen for T_CGHT_INFO and residual T_GYSHT_INFO blockers; do not model yet. |
| fund_daily_or_loan_residual | 39 | partially_assetized_management_snapshot_residual | assetized_except_blocked_tail | none; do not open another fund/loan lane unless blocked-tail recovery is explicitly required. |
| tender_registration_residual | 1168 | pre_project_auxiliary_fact | defer_unless_tender_scope_confirmed | defer; screen later only if owner wants tender history. |
| document_admin_residual | 3754 | business_auxiliary_information | no_core_fact_assetization_now | defer; optionally build document index only after document-center target model is confirmed. |
| attendance_hr_residual | 2709 | out_of_scope_hr_fact | exclude_from_construction_migration | discard for current migration; revisit only in a dedicated HR migration objective. |
| unknown_or_unmapped_family | 28784 | mostly_blocked_or_low_confidence | do_not_bulk_assetize | no bulk lane; use targeted screens only if a table becomes business-critical. |

## Evidence By Family

### payment_request_residual

- rows: `5948`
- layer: `core_business_fact_candidate`
- top tables: `{"C_ZFSQGL": 4779, "C_ZJGL_GCKZF": 858, "T_FK_Supplier": 311}`
- evidence: C_ZFSQGL direct residual screen: raw=13646, already_assetized=12284, residual_loadable=0, blocked=1362
- reason: All rows meeting project, partner, positive amount, and non-deleted rules are already in outflow_request_sc_v1.
- decision: `no_further_assetization`
- next action: none

### supplier_or_purchase_residual

- rows: `2607`
- layer: `mixed_master_and_business_fact`
- top tables: `{"T_Base_CooperatCompany": 2055, "T_CGHT_INFO": 92, "T_GYSHT_INFO": 460}`
- evidence: T_GYSHT_INFO supplier contracts already have a 5301-row supplier_contract asset lane; T_Base_CooperatCompany is partner/master-data oriented.
- reason: Most remaining rows are master-data approvals or blocked supplier-contract rows. The only plausible uncovered business-fact slice is T_CGHT_INFO purchase-contract residue.
- decision: `screen_only_for_T_CGHT_INFO_then_decide`
- next action: open read-only screen for T_CGHT_INFO and residual T_GYSHT_INFO blockers; do not model yet.

### fund_daily_or_loan_residual

- rows: `39`
- layer: `partially_assetized_management_snapshot_residual`
- top tables: `{"ZJGL_ZCDFSZ_FXJK_JK": 1, "ZJGL_ZJSZ_DKGL_DKDJ": 38}`
- evidence: Fund/loan screen: raw=873, project_financing=318, management_snapshots=496, blocked=59; financing_package=legacy_financing_loan_sc_v1 generated=318; fund_daily_package=legacy_fund_daily_snapshot_sc_v1 generated=496
- reason: Project loan/borrowing facts are in legacy_financing_loan_sc_v1 and user-required fund daily snapshots are in legacy_fund_daily_snapshot_sc_v1. Remaining fund-family rows are blocked tail records.
- decision: `assetized_except_blocked_tail`
- next action: none; do not open another fund/loan lane unless blocked-tail recovery is explicitly required.

### tender_registration_residual

- rows: `1168`
- layer: `pre_project_auxiliary_fact`
- top tables: `{"BGGL_ZTBJHT_TBBM_TBBMFSQ": 54, "P_ZTB_GCBMGL": 1114}`
- evidence: Tender registration rows are pre-contract/pre-project business-development information.
- reason: Not required for current project execution reconstruction. Could become useful only if tender/business-development history is in scope.
- decision: `defer_unless_tender_scope_confirmed`
- next action: defer; screen later only if owner wants tender history.

### document_admin_residual

- rows: `3754`
- layer: `business_auxiliary_information`
- top tables: `{"BGGL_TZXX_WJPYCJ": 1476, "BGGL_XZD_YZSYSPB": 1584, "SGZL_RZRJ": 694}`
- evidence: Seal use, document review, and archive/photo management. Attachment URL backfill already covers deterministic linked file records.
- reason: Administrative documents are auxiliary evidence, not core project/accounting/contract facts. Model design should wait for a document-center requirement.
- decision: `no_core_fact_assetization_now`
- next action: defer; optionally build document index only after document-center target model is confirmed.

### attendance_hr_residual

- rows: `2709`
- layer: `out_of_scope_hr_fact`
- top tables: `{"BGGL_HBZJ_XZD_QJXJSPB": 909, "BGGL_KQTJ_YTWC": 1109, "BGGL_XZ_JXDJ_ZB": 691}`
- evidence: Leave, outing, and performance approval rows.
- reason: HR facts do not support the current old-business-fact to construction project model reconstruction objective.
- decision: `exclude_from_construction_migration`
- next action: discard for current migration; revisit only in a dedicated HR migration objective.

### unknown_or_unmapped_family

- rows: `28784`
- layer: `mostly_blocked_or_low_confidence`
- top tables: `{"BGGL_XZ_GZ": 233, "CWGL_FYBX": 934, "C_JFHKLR_TH_ZCDF": 2550, "C_JXXP_DKDJ_New": 213, "C_JXXP_XXKPDJ": 350, "C_JXXP_ZYFPJJD": 19707, "T_KK_SJTHB": 2387, "ZJGL_BZJGL_Branch_SBZJTH": 245, "ZJGL_BZJGL_Pay_FBZJ": 341, "ZJGL_WJZ_WJZDJB": 310}`
- evidence: Largest slice is C_JXXP_ZYFPJJD, already screened as mostly missing counterparty evidence; other slices include zero-amount refunds, residual expense/deposit rows, and miscellaneous approvals.
- reason: Bulk migration would weaken source-fact requirements. Only table-specific screens may promote small slices.
- decision: `do_not_bulk_assetize`
- next action: no bulk lane; use targeted screens only if a table becomes business-critical.

## Next Executable Lane

- lane: `supplier_or_purchase_residual_screen`
- mode: `read_only_screen_first`
- scope: `T_CGHT_INFO, T_GYSHT_INFO residual blockers`
- reason: payment residual has no loadable rows and project financing facts are now assetized; supplier/purchase is the next remaining classified business family that may still contain an uncovered purchase-contract slice.

## Operating Judgment

Do not open another bulk migration lane from the remaining workflow rows.
Only table-specific read-only screens should promote further data into model or XML work.
The current best next step is a supplier/purchase residual source-table screen, not another payment request or fund/loan lane.
