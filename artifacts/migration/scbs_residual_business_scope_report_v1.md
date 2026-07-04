# SCBS Residual Business Scope Report

Status: `PASS`

## Summary

| Fact Family | Classification | Rows | Amount |
| --- | --- | ---: | ---: |
| payment | counterparty_or_remark_only | 4 | 970900.00 |
| payment | legacy_department_or_business_bucket_only | 1111 | 38167981.03 |
| supplier_contract | legacy_business_entity_or_department_only | 9 | 623832.00 |

## Judgment

- No residual row has explicit project ID/name evidence in the inspected legacy fields.
- Payment residual rows mostly have legacy `bm` values. This is treated as department/business-bucket evidence, not a project anchor.
- Supplier contract residual rows only expose business entity/department text and supplier names, not project anchors.
- These rows remain audit residuals unless the business owner confirms a target project or defines an enterprise-level target document for them.
