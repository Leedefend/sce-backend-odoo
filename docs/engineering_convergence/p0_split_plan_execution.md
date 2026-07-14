# P0 Split Plan Execution

Date: 2026-07-14
Branch: `main`
Tracked issue: `#1029`

## Decision

`split_plan_queue.md` remains generated from the complexity budget report. This
document is the accountable execution plan and current mainline status for the
three original P0 split-plan files.

The original P4-P0-01, P4-P0-02, and P4-P0-03 sequence has completed on
mainline. The generated queue now has one remaining P0 file:
`frontend/apps/web/src/pages/ContractFormPage.vue` at 5939 lines. It is below
the stage target of 6000 lines and remains under a no-regrowth evidence guard;
future work should be driven by behavior coverage and side-effect maps, not by
mechanical line-count reduction.

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
| `frontend/apps/web/src/views/BusinessConfigSurfaceView.vue` | P4-P0-02 split completed: current slices extracted formatters, snapshot remediation, navigation lookup, scoped styles, start/coverage/audit/approval/version/editor panels, shared field-chip editor, approval/version/snapshot/field-editor/coverage/workbench composables, and workbench utilities; route component reduced from 5447 to 1486 lines and exited the generated P0 split-plan queue. | `@Leedefend` | Local and remote gates passed |
| `frontend/apps/web/src/pages/ContractFormPage.vue` | P4-P0-03 split completed on mainline: shared contract form types/constants, action parsing/navigation helpers, contract record helpers, field/date/relation display helpers, access-policy normalization, relation descriptor/search helpers, one2many pure value/helpers, workflow parsing/statusbar helpers, UI label helpers, form-config/layout helpers, native-layout/descriptor/modifier helpers, value helpers, focused runtimes, and child panels extracted; route component is currently 5939 lines without changing product behavior. | `@Leedefend` | PR `#1032` merged with remote `quality_gate` success; local `ci.local.quick` evidence reports `contract_form_split_evidence lines=5939`; latest `origin/main` workflow-run evidence for `7d2f86e` still needs to be attached |

## Mainline Evidence Snapshot

| Item | Current mainline fact | Evidence |
| --- | --- | --- |
| P4-P0-01 | `Makefile` is 272 lines and no longer appears in `split_plan_queue.md`. | PR `#1031` merged as `d5c74cf6`; `quality_gate` succeeded on PR head. |
| P4-P0-02 | `BusinessConfigSurfaceView.vue` is 1486 lines and no longer appears in `split_plan_queue.md`. | PR `#1032` merged as `57b8175f`; `quality_gate` succeeded on PR head. |
| P4-P0-03 | `ContractFormPage.vue` is 5939 lines and remains the only generated P0 file. | PR `#1032` merged as `57b8175f`; `scripts/ci/verify_contract_form_split_evidence.py` reports `lines=5939`. |
| Contract governance baseline | `contract_governance.py` is 1370 lines after responsibility-helper extraction. | PR `#1052` merged as `b9d9e8cf`; `quality_gate` succeeded on PR head. |
| UI contract v2 baseline | `ui_contract_v2.py` is 3518 lines after helper extraction. | PR `#1053` merged as `815697e`; `quality_gate` succeeded on PR head. |
| ActionView baseline | `ActionView.vue` is 3681 lines after pure helper extraction and responsibility map guard. | PR `#1054` merged as `7d2f86e`; latest `origin/main` workflow-run evidence still needs to be attached. |

## Current Next Step

Do not start another P4-P0 mechanical split from this plan. The next execution
focus is evidence closure for Phase 5/6: core amount calculation tests,
permission and project-isolation verification, backup/restore drill,
performance baseline, and controlled pilot readiness.
