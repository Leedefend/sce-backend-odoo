# Test Layering Policy

This policy defines which validation assets run at each decision point during v1.1 convergence.

## Decision Gates

| Gate | Purpose | Required Entry |
| --- | --- | --- |
| PR gate | Fast confidence for every code review. | `make ci` |
| Integration gate | Prove Odoo/runtime compatibility before merging risky backend work. | `make test.odoo.integration` |
| Release gate | Prove productization and browser flows before release or deployment. | `make test.all` |
| Nightly gate | Run long browser and business-chain checks without slowing every PR. | `make test.e2e` plus approved long-running suites |

## Mandatory PR Gate

`make ci` is intentionally bounded. It must stay fast enough for regular PR use and currently includes:

- Production mutation guard.
- High-confidence secret scan.
- Test inventory freshness check.
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
