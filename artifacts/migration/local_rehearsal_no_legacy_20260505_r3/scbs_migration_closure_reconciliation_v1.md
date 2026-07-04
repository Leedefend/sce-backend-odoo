# SCBS Migration Closure Reconciliation

Status: `PASS`

| Fact Family | Source Rows | Source Amount | Formal Rows | Formal Amount | Residual Rows | Residual Amount | Delta | Status |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| payment | 9098 | 355521662.21 | 9098 | 355521662.21 | 0 | 0.00 | -0.00 | PASS_STRICT_AMOUNT_CLOSED |
| supplier_contract | 1583 | 271345661.07 | 1583 | 271345661.07 | 0 | 0.00 | 0.00 | PASS_STRICT_AMOUNT_CLOSED |
| stock_in | 700 | 88592370.17 | 697 | 88601224.17 | 0 | 0.00 | -8854.00 | PASS_WITH_HEADER_LINE_POLICY_DELTA |
| fund_daily | 3798 | 1290762428.64 | 3798 | 1290762428.64 | 0 | 0.00 | 0.00 | PASS_ENTERPRISE_DOCUMENT_CLOSED |
| inactive_residual | 44 | 14089139.36 | 0 | 0.00 | 44 | 14089139.36 | 0.00 | PASS_ARCHIVED_RESIDUAL_REGISTERED |

## Guard Checks

- SCBS formal non-direct rows: payment=0, payment_adjustment=0, enterprise_fact=0, contract=0, stock_in=0
- SCBS material mappings not confirmed: 0
- SCBS enterprise fund daily project-bound rows: 0
- SCBS enterprise fund daily missing business entity rows: 0
- Source duplicate checks: {"contract_source_duplicates": 0, "enterprise_fact_source_duplicates": 0, "fund_daily_source_duplicates": 0, "payment_adjustment_source_duplicates": 0, "payment_source_duplicates": 0, "stock_source_duplicates": 0}

Stock-in delta is expected: formal amount follows legacy line facts, while source staging amount is the header signal.
