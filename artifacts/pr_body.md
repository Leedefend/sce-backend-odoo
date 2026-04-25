## Summary

- Exposes history-continuity finance ledger surfaces in `smart_construction_core`.
- Adds replay-chain steps for payment request outflow state activation, approved/done recovery, and project lifecycle continuity.
- Records migration alignment decisions and attaches generated replay adapter payload/result artifacts.

## Architecture Impact

- Keeps changes inside the construction domain module and migration/ops evidence lanes.
- Does not change `login -> system.init -> ui.contract`.
- Does not modify platform core intent/router/contract-engine modules.
- Adds Odoo native list/form/search/menu surfaces for finance-center usability after historical replay.

## Layer Target

- Domain Layer: `addons/smart_construction_core`
- Operations/Migration Layer: `scripts/migration`, `artifacts/migration`, `docs/migration_alignment`, `docs/ops`

## Affected Modules

- `addons/smart_construction_core`
- `scripts/migration`
- `artifacts/migration`
- `docs/migration_alignment`
- `docs/ops`
- `Makefile`

## Reason

Prepare the history continuity promotion work for merge into `main` with separated implementation, documentation, and evidence artifacts.

## Verification

- Local branch preflight passed:
  - `pwd`
  - `git rev-parse --show-toplevel`
  - `git branch --show-current`
  - `git status --short`
- Worktree was clean before PR preparation.
- No additional runtime validation was run in this PR-prep step.

## Commits

- `58791e11 feat(finance): expose history continuity ledger views`
- `b3d4cf9b feat(migration): add history continuity promotion replay chain`
- `6e4be64a docs(migration): record history continuity promotion decisions`
- `8f4888ef chore(migration): add history continuity promotion artifacts`
