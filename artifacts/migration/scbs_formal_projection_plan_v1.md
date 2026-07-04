# SCBS Formal Projection Plan

This is a dry-run plan. It does not create formal business documents.

| Fact Family | Active Rows | Amount | Target Model | New Rows | Status |
| --- | ---: | ---: | --- | ---: | --- |
| fund_daily | 3798 | 1290762428.64 | reporting_snapshot | 3798 | reporting_only_no_formal_write_target |
| payment | 9107 | 359251657.39 | sc.payment.execution | 9107 | PARTIAL_READY_PROJECT_BUCKET_POLICY_REQUIRED |
| stock_in | 700 | 88592370.17 | sc.material.inbound | 700 | READY_WITH_LINE_AMOUNT_AND_MISMATCH_AUDIT_POLICY |
| supplier_contract | 1585 | 273565406.25 | sc.general.contract | 1585 | PARTIAL_READY_PROJECT_BUCKET_POLICY_REQUIRED |

## Current Decision

- Active staging facts are dimension-ready.
- Payment, supplier-contract, and stock-in rows with confirmed projects are ready for source-tagged formal projection.
- Rows without legacy project cannot be fully written to the current formal target models until a project-bucket policy is accepted.
- Stock-in projection must use line amount and retain header/line differences as audit evidence.
- Fund daily remains reporting snapshot until a formal target model is selected.
