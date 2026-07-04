# History Continuity Usability Probe v1

Status: PASS

## Scope

Read-only continuity probe after historical replay or rehearsal.
This probe does not mutate business data.

## Current Counts

```json
{
  "legacy_users": 101,
  "partner_l4_anchors": 0,
  "contract_counterparty_partners": 0,
  "receipt_counterparty_partners": 0,
  "project_anchors": 0,
  "project_member_carrier": 0,
  "contract_headers": 0,
  "contract_summary_lines": 0,
  "supplier_contract_headers": 0,
  "supplier_contract_lines": 0,
  "receipt_core_requests": 0
}
```

## Decision

`history_continuity_conditional_missing_runtime_facts`

## Notes

- This probe only verifies replayed historical facts are present in runtime/carrier models.
- Promotion from carrier rows into runtime business ownership remains a later batch.
