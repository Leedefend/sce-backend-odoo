# SCBS Formal Projection Policy Preflight

This report checks active SCBS staging facts only. It does not write formal business documents.

## Conclusion

- Active dimension mapping is complete: formal blockers are now policy gates, not missing entity/project/partner/material mappings.
- Some active facts have no legacy project, while the target formal models require `project_id`; these rows need an explicit project-bucket policy before full formal write.
- Rows with a confirmed project can be projected as source-tagged SCBS facts under the supplement/reference policies below.
- Stock-in must be projected from line detail with mismatch audit notes; it must not be projected from header totals alone.
- Fund daily remains reporting-only because it is a balance snapshot, not an operational posting.

## Gate Matrix

| Fact Family | Rows | Amount | Target | Gate | Blocker | Evidence |
| --- | ---: | ---: | --- | --- | --- | --- |
| payment | 9107 | 359251657.39 | sc.payment.execution | PROJECT_BUCKET_POLICY_REQUIRED | target_project_id_required_but_legacy_project_missing | strict_exact_rows=0 strict_exact_amount=0.00; broad_partner_amount_rows=214 broad_partner_amount=18179852.98 |
| supplier_contract | 1585 | 273565406.25 | sc.general.contract | PROJECT_BUCKET_POLICY_REQUIRED | target_project_id_required_but_legacy_project_missing | source_key_existing_rows=0 source_key_amount=0.00; doc_reference_matches=1 doc_reference_amount_general=0.00 doc_reference_amount_construction=1.00 |
| stock_in | 700 | 88592370.17 | sc.material.inbound | READY_WITH_LINE_AMOUNT_AND_MISMATCH_AUDIT_POLICY | none; line_amount_is_business_fact_and_mismatches_are_audited | active_headers=700 active_lines=2205 line_amount=88601224.17 mismatch_headers=5 mismatch_amount_abs=8854.00 headers_without_lines=3 headers_without_lines_amount=.00 |
| fund_daily | 3798 | 1290762428.64 | reporting_snapshot | REPORTING_ONLY_NOT_FORMAL_WRITE | no_operational_posting_target | fund_daily is a balance snapshot, not an execution voucher |

## Recommended Projection Policies

- `payment`: create source-tagged SCBS payment execution as project-level supplement; do not merge into existing payment_request
- `supplier_contract`: use legacy_source_model+legacy_record_id as identity; keep document_no/contract_no as source reference only
- `stock_in`: create source-tagged inbound headers from active SCBS headers and lines; amount follows line total, header mismatch retained as audit note
- `fund_daily`: retain as reporting/balance snapshot attached to confirmed business entity until target semantics are defined

## Required Target Field Gaps

| Fact Family | Missing Project | Missing Partner | Missing Business Entity |
| --- | ---: | ---: | ---: |
| payment | 1115 | 12 | 5987 |
| supplier_contract | 9 | 0 | 240 |
| stock_in | 0 | 4 | 0 |
| fund_daily | 3798 | 3798 | 0 |

## Stock-In Mismatch Examples

| Legacy ID | Document No | Date | Supplier | Project | Header Amount | Line Amount | Diff | Lines |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| aac5dcdee15d485a9cc5b5230ffd777c | RKD-202303402301 | 2023-03-08 |  |  | .00 | 8000.00 | 8000.00 | 1 |
| cbd42f2989994a189c5d831d8e5dabdb | RKD-202303482150 | 2023-03-09 | 米测试供应商 |  | .00 | 441.00 | 441.00 | 1 |
| fe818240d83e441b84517990a9c4d8cf | RKD-202303401410 | 2023-03-08 |  |  | .00 | 276.00 | 276.00 | 1 |
| 3dedcddffd3244a49ff6fc504eb36365 | RKD-202303082048 | 2023-03-29 | 中国建筑一局（集团）有限公司 |  | .00 | 104.00 | 104.00 | 3 |
| 2ab2206e7f144924914de768c2040f43 | RKD-202303512041 | 2023-03-28 | 西北综合勘察设计研究院项目管理公司 |  | .00 | 33.00 | 33.00 | 1 |

## Stock-In Headers Without Lines

| Legacy ID | Document No | Date | Supplier | Project | Header Amount |
| --- | --- | --- | --- | --- | ---: |
| 6208f82be70c456e9d10f1297f2f69ce | RKD-202303122300 | 2023-03-08 |  |  | .00 |
| 5c53ccbef39d4f2caafb80c0c9694fcd | RKD-202303472040 | 2023-03-29 | 陕西省煤炭物资供应公司 |  | .00 |
| 14ab8241292345458c56000305af8adf | RKD-202303361850 | 2023-03-09 |  |  | .00 |
