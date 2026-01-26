# Smart Core Upgrade Deadlock Report

## Summary
A deadlock can occur when upgrading `smart_construction_core` while installing `smart_core` in the same upgrade run. The failure was observed during contract stabilization when `smart_construction_core` attempted to install `smart_core` as a dependency.

## Reproduction (best effort)
Use dev environment only:

```
CODEX_NEED_UPGRADE=1 CODEX_MODULES=smart_construction_core make codex.fast
```

Observed behavior: upgrade fails with `psycopg2.errors.DeadlockDetected` during registry initialization.

## Evidence
- Previous run logs:
  - `artifacts/codex/codex/portal-autonomous-v1/fast-baseline/codex_fast_upgrade.log`
  - `artifacts/codex/codex/portal-autonomous-v1/fast-baseline/codex_fast_upgrade_retry1.log`

## Deadlock symptoms
- `Failed to initialize database`
- Deadlock during foreign key creation:
  - `psycopg2.errors.DeadlockDetected: deadlock detected`
  - `self.check_foreign_keys(cr)` -> `sql.add_foreign_key(...)`

## Suspected lock chain
- Module graph loads `smart_construction_core` and triggers install of `smart_core`.
- Concurrent registry/table updates during module graph load can collide with FK creation.

## Proposed mitigations
1. Install `smart_core` in a separate upgrade step (avoid mixed graph upgrade).
2. Reduce concurrent writes during registry initialization (single-worker upgrade).
3. If possible, split schema changes and data updates into separate transactions.

## Status
- Not root-caused; report provided for tracking.
- Workaround used: avoid dependency-based install during upgrade; fallback logic added instead.

