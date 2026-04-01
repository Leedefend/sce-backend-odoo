# ITER-2026-04-01-559

- status: PASS
- mode: screen
- layer_target: Frontend Layer
- module: primary toolbar visibility gating
- risk: medium

## Decision

- bounded_followup_scope_or_stop: `bounded_followup_scope`
- decision: `PASS_WITH_BOUNDED_STRUCTURAL_FOLLOWUP`
- reason: the remaining visibility candidate can be reduced to a single local rule in `PageToolbar.vue`: if optimization mode hides the `search` section but the primary toolbar still has a visible sort summary, the toolbar should remain mounted instead of disappearing entirely.

## Bounded Follow-Up Scope

- file: `frontend/apps/web/src/components/page/PageToolbar.vue`
- responsibility: `showPrimaryToolbar` gating only
- allowed effect: preserve the primary toolbar when `showSortBlock` is still true
- forbidden effect: do not change optimization section ordering, sort behavior, or any action callbacks

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-01-559.yaml`: PASS

## Next Iteration Suggestion

- open a dedicated structural implementation batch limited to the `showPrimaryToolbar` gate and verify it with the standard frontend gate and trusted list smoke
