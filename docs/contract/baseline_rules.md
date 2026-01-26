# Contract Baseline Rules

## Purpose
Baseline snapshots define the expected contract output for critical cases. They are reviewed artifacts, not runtime logs.

## Contract versioning
- `contract_version` uses a major-only token (for now: `v1`).
- Backward-compatible changes (additive fields) keep the same major.
- Breaking changes must bump the major (e.g., `v2`) and update snapshots.

## When to update
- Contract schema changes (new fields, renamed keys).
- Intentional UI contract behavior changes (buttons, layout, permissions).
- Model/meta updates that are expected to change snapshots.

## When not to update
- Pure runtime noise (timestamps, trace ids, session data).
- Environment-specific values (server time, transient IDs).

## Process
1. Run `make gate.contract DB=<db>` to generate candidate snapshots.
2. Review diffs in the gate output.
3. If the changes are expected, update baselines:
   - `make gate.contract.bootstrap DB=<db>` (local only)
   - If you want a clean local exit after bootstrapping: `make gate.contract.bootstrap-pass DB=<db>`
   - `git add docs/contract/snapshots`
4. Commit with a message explaining the reason.

## Ownership
- Baseline updates must be reviewed by a code owner for contract schema changes.
