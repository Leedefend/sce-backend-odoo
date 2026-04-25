# History Payment Request Outflow State Activation Report v1

Status: `PASS`

Task: `ITER-2026-04-25-HISTORY-CONTINUITY-PROMOTION-A-001`

## Decision

Use a dedicated historical promotion lane for `outflow_request_core`:

- promote `payment.request(state)` from `draft` to `submit`
- only for migrated `outflow_request_core` rows with historical workflow audit facts
- do not write `tier.review`
- do not write `validation_status`
- do not trigger live approval callbacks
- do not enforce live funding gate during this historical activation batch

## Inputs

- outflow asset rows: `12284`
- workflow-covered outflow rows: `12247`
- workflow-uncovered outflow rows: `37`
- workflow audit rows on outflow lane: `45693`

## Write Result

- first execution promoted rows: `12247`
- replay-safe rerun:
  - `promoted_rows = 0`
  - `skipped_non_draft = 12247`
- blocked rows: `0`

## Business Usable Result

Command:

```bash
DB_NAME=sc_demo make history.business.usable.probe
```

Result:

- `status = PASS`
- `decision = history_business_usable_ready`
- `gap_count = 0`

Payment request state distribution:

```json
{
  "draft": 15555,
  "submit": 12247
}
```

## Boundary

This batch explicitly did not:

- import legacy approvals into `tier.review`
- mark historical rows as `validated`
- reconstruct live reviewer queues
- mark historical rows as `approved` or `done`

## Artifacts

- `artifacts/migration/history_payment_request_outflow_state_activation_payload_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_state_activation_write_result_v1.json`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_state_activation_rollback_targets_v1.csv`
- `/tmp/history_continuity/sc_demo/adhoc/history_payment_request_outflow_state_activation_blocked_rows_v1.csv`
