# Business Fact Acceptance Bundle Summary v1

Status: FAIL

## Summary

```json
{
  "artifact_root": "artifacts/migration/business_fact_upgrade",
  "postcheck": {
    "presence": "missing",
    "status": "MISSING",
    "contract_total": null,
    "income_contracts": null,
    "expense_contracts": null,
    "contract_lines": null,
    "visible_fact_mismatches": null,
    "visible_balance_observations": null
  },
  "cleanup": {
    "presence": "missing",
    "status": "MISSING",
    "visible_balance_observations": null,
    "classification_counts": null,
    "invoice_receipt_mismatches": null,
    "db_writes": null
  },
  "legacy_source": {
    "presence": "skipped",
    "status": "SKIPPED",
    "source_contract_rows_found": null,
    "receipt_linked_rows": null,
    "invoice_linked_rows": null,
    "decisions": null
  }
}
```

## Errors

```json
[
  {
    "error": "missing_required_artifact",
    "artifact": "fresh_db_business_fact_replay_postcheck_result_v1.json"
  },
  {
    "error": "missing_required_artifact",
    "artifact": "business_fact_visible_balance_cleanup_result_v1.json"
  },
  {
    "error": "acceptance_step_failed",
    "step": "postcheck",
    "status": "MISSING"
  },
  {
    "error": "acceptance_step_failed",
    "step": "cleanup",
    "status": "MISSING"
  }
]
```

## Decision

`STOP_REVIEW_REQUIRED`
