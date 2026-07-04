# SCBS Unified Residual Register

## Summary

| Category | Rows | Amount | Reason | Target |
| --- | ---: | ---: | --- | --- |
| payment_no_project | 0 | 0.00 | no_source_project_clue | sc.legacy.enterprise.business.fact |
| payment_negative_project_confirmed | 0 | 0.00 | negative_payment_requires_refund_or_reversal_target | none |
| supplier_contract_no_project | 0 | 0.00 | no_source_project_clue | sc.legacy.enterprise.business.fact |
| stock_in_zero_amount_no_line | 3 | 0.00 | zero_amount_no_legacy_lines | none |
| inactive_non_business_or_dirty_residual | 33 | 8139399.00 | archived_from_projection_pool | none |

## Policy

- Residual rows are not discarded; they remain source-identifiable audit facts.
- No-project rows are not forced into direct projects without source-chain evidence.
- No-project payment/contract rows written to `sc.legacy.enterprise.business.fact` are no longer residual rows.
- Negative payment rows are not written into the non-negative payment execution model.
- Negative payment rows written to `sc.legacy.payment.adjustment.fact` are no longer residual rows.
- Fund daily rows are now enterprise business documents and are not residual rows.
- Zero-amount stock-in headers without legacy lines do not create empty inbound documents.

Detail CSV: `artifacts/migration/scbs_unified_residual_register_v1.csv`
