# Fresh DB Replay Manifest Execution Refresh Report V1

Status: PASS

Task: `ITER-2026-04-15-FRESH-DB-REPLAY-MANIFEST-RECEIPT-LANE-NORMALIZE`

## Scope

Refresh the replay manifest with already completed fresh database execution
results. This batch performs no database reads or writes.

## Result

- execution lanes refreshed: `6`
- prerequisite results attached: `1`
- contract header historical rows: `1332`
- contract header retry rows: `57`
- contract header total rows: `1389`
- receipt core rows: `1683`
- manifest default-run lanes: `0`
- DB writes: `0`

## Decision

`fresh_db_replay_manifest_execution_refreshed`

## Next

open next migration lane after receipt core replay
