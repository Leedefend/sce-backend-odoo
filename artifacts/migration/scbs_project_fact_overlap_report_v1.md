# SCBS Project-Level Fact Overlap Report

## Summary

| source_table | fact_family | staged_rows | staged_amount | overlap_method | overlap_rows | overlap_amount | projection_policy |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D_SCBSJS_ZJGL_ZJSZ_ZJRBB | fund_daily | 3798 | 1290762428.64 | enterprise_fund_daily_source_id_unique | 3798 | 1290762428.64 | enterprise_business_document_written_no_project_binding |
| T_FK_Supplier | payment | 9130 | 364696413.39 | payment_project_partner_date_amount_exact | 0 | 0.0 | requires_payment_duplicate_review |
| T_RK_RKD | stock_in | 703 | 90338220.17 | material_inbound_legacy_fact_id_unique | 697 | 88601224.17 | formal_material_inbound_written_by_legacy_fact_id |
| T_GYSHT_INFO | supplier_contract | 1592 | 274514199.25 | contract_legacy_id_exact | 0 | 0.0 | block_duplicates_by_legacy_contract_id |

## Interpretation

- Supplier contracts can be checked by exact legacy contract ID and document number.
- Supplier payments have no direct formal legacy ID in `payment.request`; current check is approximate by project, partner, date, and amount.
- Material inbound is formally written by legacy fact ID; duplicate risk is controlled by source identity.
- Fund daily is now projected as enterprise business documents on business entity, not project; SCBS project binding must remain zero.
