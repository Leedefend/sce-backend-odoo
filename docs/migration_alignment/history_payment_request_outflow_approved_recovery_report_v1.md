# History Payment Request Outflow Approved Recovery Report v1

Status: `PASS`

Task: `ITER-2026-04-25-HISTORY-CONTINUITY-PROMOTION-B-001`

## Decision

Use the pre-existing downstream approval judgment as the only source for
historical `submit -> approved` recovery on `outflow_request_core`.

Approved facts used:

- `historical_approved_by_downstream_business_fact`
- `historical_approved`

Explicitly excluded:

- `tier.review`
- `validation_status`
- live reviewer queue
- approval callbacks

## Source of Truth

This batch reuses the frozen analysis artifacts already present in the repo:

- `artifacts/migration/legacy_payment_approval_downstream_fact_screen_rows_v1.csv`
- `artifacts/migration/legacy_payment_approval_downstream_fact_screen_result_v1.json`

Frozen high-confidence rule:

```text
target_lane=outflow_request and actual_outflow_count > 0
=> historical_approved_by_downstream_business_fact
```

## Adapter Result

- payload rows: `12201`
- fact split:
  - `historical_approved_by_downstream_business_fact = 12194`
  - `historical_approved = 7`

## Write Result

- input rows: `12201`
- promoted rows: `12201`
- skipped non-submit: `0`
- blocked rows: `0`

## Runtime Result

Current `outflow_request_core` state distribution in `sc_demo`:

```json
{
  "approved": 12201,
  "submit": 46,
  "draft": 37
}
```

Validation status distribution remains:

```json
{
  "no": 12284
}
```

## Boundary

This batch restores historical business state only.

It does not claim that the new approval runtime was reconstructed.

The following remain untouched:

- `tier.review`
- `validation_status`
- live callback chain
- reviewer identity/runtime visibility

## Artifacts

- `artifacts/migration/history_payment_request_outflow_approved_recovery_payload_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_approved_recovery_write_result_v1.json`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_approved_recovery_rollback_targets_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_approved_recovery_blocked_rows_v1.csv`
