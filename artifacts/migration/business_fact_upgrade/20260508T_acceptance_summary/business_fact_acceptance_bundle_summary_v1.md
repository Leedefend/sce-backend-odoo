# Business Fact Acceptance Bundle Summary v1

Status: PASS

## Summary

```json
{
  "artifact_root": "/home/odoo/workspace/sce-backend-odoo/artifacts/migration/business_fact_upgrade/20260508T_acceptance_summary",
  "postcheck": {
    "presence": "present",
    "status": "PASS",
    "contract_total": 6850,
    "income_contracts": 1541,
    "expense_contracts": 5309,
    "contract_lines": 6566,
    "visible_fact_mismatches": 0,
    "visible_balance_observations": 5
  },
  "cleanup": {
    "presence": "present",
    "status": "PASS",
    "visible_balance_observations": 5,
    "classification_counts": {
      "legacy_visible_negative_balance_without_transaction_fact": 3,
      "legacy_visible_partial_or_closed_balance_without_transaction_fact": 2
    },
    "invoice_receipt_mismatches": 0,
    "db_writes": 0
  },
  "legacy_source": {
    "presence": "present",
    "status": "PASS",
    "source_contract_rows_found": 5,
    "receipt_linked_rows": 0,
    "invoice_linked_rows": 0,
    "decisions": {
      "legacy_contract_header_only_no_linked_transaction_detail": 5
    }
  }
}
```

## Errors

```json
[]
```

## Decision

`business_fact_acceptance_bundle_passed`
