# History Contract Core Gap Report v1

Status: ACTIVE

Task: `ITER-2026-04-25-HISTORY-CONTRACT-CORE-GAP-AUDIT-001`

## Scope

Read-only audit of `contract_sc_v1` coverage against the original contract
header asset package.

This audit freezes:

- how many contract headers exist in the asset package;
- how many entered bounded historical payloads;
- how many entered retry/special slices;
- how many never entered any replay payload at all.

## Coverage Snapshot

- asset rows: `1492`
- historical bounded payload rows: `1332`
- special 12-row payload: `12`
- bounded payload union: `1344`
- retry 57 rows: `57`
- bounded + retry coverage: `1401`
- never-reached asset rows: `91`

## Key Findings

1. The current historical bounded chain is not the full `contract_sc_v1` asset.
   It covers `1344` rows, not `1492`.
2. Even after adding the dedicated `57 retry` lane, total historical/retry
   coverage reaches `1401`, still leaving
   `91` asset rows never entering any replay lane.
3. The unreached rows are not structurally blank:
   - project refs present: `91`
   - partner refs present: `91`
   - master partner refs: `45`
   - contract counterparty refs: `46`

## Decision

`Batch-UR-A` is now frozen into three concrete sub-gaps:

1. `special_slice_gap_12`
2. `retry_lane_gap_57`
3. `never_reached_asset_gap_91`

`Group B` downstream replay must stay blocked until these are resolved in order.

## Artifacts

- JSON audit: `artifacts/migration/history_contract_core_gap_audit_v1.json`
- unreached CSV: `artifacts/migration/ur_a_contract_unreached_asset_rows_v1.csv`
