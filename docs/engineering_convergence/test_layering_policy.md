# Test Layering Policy

This policy defines which validation assets run at each decision point during v1.1 convergence.

## Decision Gates

| Gate | Purpose | Required Entry |
| --- | --- | --- |
| Local quick gate | Fast confidence for small frontend or architecture-boundary iterations. | `make ci.local.quick` |
| PR gate | Full local confidence before code review and remote CI. | `make ci` |
| Integration gate | Prove Odoo/runtime compatibility before merging risky backend work. | `make test.odoo.integration` |
| Release gate | Prove productization and browser flows before release or deployment. | `make test.all` |
| Nightly gate | Run long browser and business-chain checks without slowing every PR. | `make test.e2e` plus approved long-running suites |

## Mandatory PR Gate

`make ci.local.quick` is the normal inner-loop gate for low-risk frontend and
architecture-boundary refactors. It includes:

- P0/high-risk split-plan line-count lock.
- Web Contract V2 frontend architecture boundary guard.
- P4-P0-03 contract-form split evidence freshness guard.
- Frontend page contract boundary guard.
- Frontend page contract orchestration consumption guard.
- Frontend contract consumer intrusion guard.
- Frontend lint.
- Frontend strict typecheck.
- `git diff --check`.

`make ci` is intentionally bounded. It must stay fast enough for regular PR use and currently includes:

- Production mutation guard.
- High-confidence secret scan.
- Test inventory freshness check.
- E2E fixed-scenario preflight checks for BOQ import, BOQ-to-WBS/task generation, and settlement approval.
- Python syntax check for core addons and scripts.
- Frontend lint, strict typecheck, and build.
- Contract/static frontend script checks.
- Git whitespace check.

## Release-Only Gate

Release-only gates may be slower and environment-dependent:

- Odoo install/upgrade smoke.
- Full browser productization acceptance.
- Core business-chain E2E scenarios.
- Backup/restore drills.
- Performance baselines.
- Attachment upload/download validation.

## Cleanup Rules

- A validation asset with unknown runtime must be classified before becoming a required gate.
- A duplicate guard must either be merged into a maintained gate or moved to review status.
- A stale guard that checks removed behavior must be deleted or archived in the same PR that records the reason.
- Any test touching production-like data, remote servers, or database mutation must not run inside `make ci`.
- Every required gate must have one owner and one documented failure classification.

## Current Phase 2 Findings

- The inventory is heavily weighted toward contract and governance checks.
- E2E coverage exists but must be mapped to the 12 named user journeys.
- Several shell-based assets still have unknown runtime and need classification.
- The next cleanup pass should reduce overlap in contract/governance guards before adding more checks.
