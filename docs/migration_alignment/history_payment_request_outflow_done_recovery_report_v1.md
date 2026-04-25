# History Payment Request Outflow Done Recovery Report v1

Status: `PASS`

Task: `ITER-2026-04-25-HISTORY-CONTINUITY-PROMOTION-C-001`

## Decision

Use historical paid business facts to restore `outflow_request_core` from
`approved` to `done`.

This batch does not attempt to reconstruct old settlement runtime.

It restores the minimum new-system facts needed to keep runtime semantics
coherent:

- `payment.request.state = done`
- `payment.request.validation_status = validated`
- one minimal `payment.ledger` fact per recovered request

Explicitly excluded:

- `tier.review`
- live reviewer queue
- `sc.settlement.order`
- account move / accounting replay
- approval callbacks

## Source of Truth

This batch reuses the frozen downstream payment state-sync snapshot already
present in the repo:

- `artifacts/migration/legacy_payment_approval_downstream_fact_state_sync_snapshot_v1.csv`

The recovery gate is strict:

- `old_state = done`
- `old_validation_status = validated`
- `old_ledger_count = 1`

## Adapter Result

- payload rows: `12194`
- business fact:
  - `historical_paid_by_downstream_business_fact = 12194`

## Write Result

- promoted rows: `12194`
- target state: `done`
- target validation status: `validated`
- minimal ledger rows materialized: `12194`

## Runtime Result

Current `outflow_request_core` state distribution in `sc_demo`:

```json
{
  "done": 12194,
  "approved": 7,
  "submit": 46,
  "draft": 37
}
```

## Boundary

This batch restores historical business-paid truth only.

It does not claim that the old settlement runtime was recreated.

The new `payment.ledger` rows are materialized as minimal business facts so that
new-system paid/unpaid runtime surfaces remain internally consistent.

## Artifacts

- `artifacts/migration/history_payment_request_outflow_done_recovery_payload_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_done_recovery_write_result_v1.json`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_done_recovery_rollback_targets_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_done_recovery_blocked_rows_v1.csv`
