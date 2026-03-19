# One-Week Seal-Off Plan (Week-1) v1

## Objective
- Move delivery state from “demo-ready” to “pilot-ready” within one week.

## Day 1-2: Frontend Seal-Off
- Burn down all `frontend gate` red lines (lint/typecheck/build).
- Priority files: `ActionView.vue`, `useActionViewBatchRuntime.ts`, `useActionViewGroupedRowsRuntime.ts`, `AppShell.vue`.
- Output: consistent frontend gate pass records.

## Day 2-3: Contract/Engine Closure
- Complete contract/provider-shape verification for delivery-package key scenes.
- Confirm key scenes of all 9 modules run on the scene_engine main path.
- Output: guard pass list and failure attribution.

## Day 3-4: Real Gap Backlog
- Build 3-tier gap backlog: `Blocker` / `Pilot Risk` / `Post-GA`.
- Each item must include owner, due date, and status.
- Output: trackable backlog doc and board link.

## Day 4-5: Delivery Evidence Closure
- Generate system-bound evidence for 9 modules and 4 role journeys.
- Publish one-page readiness scoreboard (commit/db/seed/pass rate).
- Output: release review package.

## Week Exit Criteria (Friday)
- All P0 blockers closed.
- No `FAIL` in the 9-module acceptance matrix.
- Delivery evidence is reproducible, auditable, and demo-ready.

