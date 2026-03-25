# Release Orchestration Surface v1

## Scope

This batch governs release operations on top of:

- Release Snapshot Promotion Lineage v1
- Edition Freeze Surface v1
- Edition Runtime Routing v1

It does not reopen FR-1 to FR-5 and does not change released navigation semantics.

## New Release Surface

Release is now represented by:

- `sc.release.action`
- `ReleaseOrchestrator.promote_snapshot(...)`
- `ReleaseOrchestrator.rollback_snapshot(...)`

## Guard Entry

- `make verify.release.action_guard ...`
- `make verify.release.orchestration_guard ...`
- `make verify.release.orchestration.v1 ...`

## Expected Outcome

- every release promotion/rollback has an action record
- source/target/result snapshots are traceable
- failure is recorded as action state, not hidden in transient runtime output
- release gate verifies orchestration, not just snapshot capability
