# P0 Split Plan Execution

Date: 2026-07-12
Branch: `topic/v1.1-engineering-convergence`
Tracked issue: `#1029`

## Decision

`split_plan_queue.md` remains generated from the complexity budget report. This document is the accountable execution plan for the three P0 split-plan files.

All P0 split-plan work has one accountable owner:

- Accountable owner: `@Leedefend`
- Review owner: `@Leedefend` through CODEOWNERS
- Implementation collaborator: optional; collaborators do not replace owner review

## P0 PR Sequence

| Sequence | PR Working Title | Accountable Owner | File | Objective | Dependency | Required Gates |
| --- | --- | --- | --- | --- | --- | --- |
| P4-P0-01 | Split root Makefile into stable included fragments | `@Leedefend` as DevOps/release owner | `Makefile` | Move implementation bodies into `make/*.mk` and scripts while preserving public target names. | None; this runs first because every later PR relies on stable local and CI gates. | `git diff --check`; `make ci`; GitHub `v1.1 quality gate / quality_gate`. |
| P4-P0-02 | Decompose business configuration surface shell | `@Leedefend` as frontend/platform owner | `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue` | Extract data adapters, workbench state, panels, and action handlers while keeping backend contracts as source of truth. | P4-P0-01 must be merged or rebased so quality gates are stable. | `git diff --check`; frontend lint/typecheck/build; `make ci`; targeted browser smoke when UI behavior changes. |
| P4-P0-03 | Decompose contract form route shell | `@Leedefend` as frontend/product owner | `frontend/apps/web/src/pages/ContractFormPage.vue` | Extract composables, section panels, footer actions, and data mapping while keeping the route component as orchestration shell. | P4-P0-02 should land first to reuse the same frontend extraction pattern. | `git diff --check`; frontend lint/typecheck/build; `make ci`; targeted browser smoke for create/edit/save flows. |

## Execution Rules

- One P0 file per PR unless a smaller shared helper is required by that same PR.
- Public behavior must remain unchanged unless the PR explicitly links a defect issue.
- Public Make target names must remain stable; target bodies may move.
- Frontend route components may orchestrate, but must not become backend contract interpreters.
- Backend contracts, menu configuration, permissions, and Odoo native structures remain backend-owned.
- Each PR must include before/after line counts for the touched P0 file.
- Each PR must include rollback instructions that restore the previous shell without data migration.

## Explicit Non-Scope

- No product feature expansion.
- No menu or permission policy redesign.
- No production deployment.
- No data migration.
- No broad visual redesign while splitting the files.
- No opportunistic cleanup of unrelated P1/P2 files.

## Acceptance Checklist Per PR

- The P0 file still passes its existing user-visible workflows.
- The route or root entrypoint is smaller and has a narrower responsibility.
- Extracted modules have clear names and single responsibilities.
- The PR body links this plan and the related split-plan item.
- `make ci` passes locally and remotely.
- CODEOWNERS review is completed by `@Leedefend`.

## Accountable Next Steps

| File | Next Step | Owner | Status |
| --- | --- | --- | --- |
| `Makefile` | P4-P0-01 split completed: root Makefile reduced from 6062 to 272 lines, target bodies moved into stable `make/*.mk` fragments, and the file exited the generated P0 split-plan queue. | `@Leedefend` | Local and remote gates passed |
| `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue` | P4-P0-02 split completed: current slices extracted formatters, snapshot remediation, navigation lookup, scoped styles, start/coverage/audit/approval/version/editor panels, shared field-chip editor, approval/version/snapshot/field-editor/coverage/workbench composables, and workbench utilities; route component reduced from 5447 to 1494 lines and exited the generated P0 split-plan queue. | `@Leedefend` | Local and remote gates passed |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | P4-P0-03 in progress: shared contract form types/constants, action parsing helpers, contract record helpers, field/date/relation display helpers, access-policy normalization, relation descriptor/search helpers, one2many pure value helpers, workflow parsing/statusbar helpers, UI label helpers, form-config helpers, native-layout/modifier helpers, and value helpers extracted; route component reduced from 13762 to 12572 lines without changing product behavior. | `@Leedefend` | Local full CI passed |
