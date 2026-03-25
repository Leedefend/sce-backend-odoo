# Release Orchestration Context Log v1

## Batch Goal

Turn release promotion and rollback into controlled, recorded release actions.

## What Changed

- added `sc.release.action`
- added `ReleaseOrchestrator`
- promotion and rollback now emit action records with result and diagnostics
- release gate now includes action/orchestration guards

## Recovery Anchor

Before changing release orchestration further, verify:

1. `make verify.release.snapshot_lineage.v1 ...`
2. `make verify.release.orchestration.v1 ...`

## Non-Goals Preserved

- no new admin UI
- no approval workflow
- no change to runtime released navigation semantics
