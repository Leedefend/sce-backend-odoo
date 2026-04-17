# Funding Carrier Fact Sync v1

## Purpose

Replay project funding carrier facts for imported contract-backed projects so
new-system payment handling can continue after legacy data import.

## Source Facts

Eligible projects must satisfy all conditions:

- imported project with `legacy_project_id`
- project code exists
- at least one non-cancelled contract
- summed non-cancelled contract `amount_final` is greater than 0
- no existing active `project.funding.baseline`

## Replay Behavior

`scripts/migration/funding_carrier_fact_sync.py` supports:

- `SYNC_MODE=check`: classify candidates and write snapshot/rollback evidence.
- `SYNC_MODE=write`: enable `funding_enabled` and create one active funding
  baseline per eligible project.

The baseline amount is the summed non-cancelled contract final amount.

## Exclusions

- Projects with zero contract sums are skipped.
- Projects with existing active funding baselines are skipped.
- No payment, settlement, account, ACL, approval, or model semantics are changed.

## Evidence

The script writes:

- `artifacts/migration/funding_carrier_fact_sync_result_v1.json`
- `artifacts/migration/funding_carrier_fact_sync_snapshot_v1.csv`
- `artifacts/migration/funding_carrier_fact_sync_rollback_v1.csv`

## 2026-04-17 Execution

Check mode before write:

- eligible_total: 642
- target_without_active_baseline_count: 642
- already_active_baseline_count: 0

Write mode:

- enabled_project_count: 642
- created_baseline_count: 642

Post-check:

- eligible_total: 642
- target_without_active_baseline_count: 0
- already_active_baseline_count: 642

Rollback-only finance submit verification confirmed the funding carrier
prerequisite is satisfied:

- `funding_enabled`: true
- `is_funding_ready`: true
- active baseline count: 1

The next blocker is outside funding facts:

```text
Unable to send message, please configure the sender's email address.
```

This is a mail/notification runtime configuration blocker raised after the
payment request reaches submit-side processing.
