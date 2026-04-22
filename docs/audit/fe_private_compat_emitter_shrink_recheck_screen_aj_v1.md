# FE Private Compat Emitter Shrink Recheck Screen AJ v1

## Goal

Freeze the strongest bounded classification statement after private compat
emitter shrink recheck.

## Fixed Architecture Declaration

- Layer Target: Frontend governance screen
- Module: private compat emitter shrink recheck
- Module Ownership: frontend scene-first contract-consumer boundary
- Kernel or Scenario: scenario
- Reason: the latest scan already froze the reduced residual set, so the next
  low-cost step is classification only

## Screen Result

- `next_candidate_family`
  - `router-and-registry private compat baseline`

- `family_scope`
  - `router private compat registration`
  - `frontend/apps/web/src/router/index.ts`
  - `sceneRegistry compat prefix recognition`
  - `frontend/apps/web/src/app/resolvers/sceneRegistry.ts`
  - `entry surfaces now fallback-only`
  - `frontend/apps/web/src/views/WorkbenchView.vue`
  - `frontend/apps/web/src/views/HomeView.vue`
  - `frontend/apps/web/src/views/MyWorkView.vue`
  - `frontend/apps/web/src/views/ProjectsIntakeView.vue`

- `reason`
  - bounded entry surfaces now prefer scene-first navigation and keep compat
    only in fallback branches
  - the most stable residual private compat baseline is now concentrated in
    router registration and sceneRegistry prefix recognition
  - this screen does not surface a new backend semantic-supply blocker

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-RECHECK-SCREEN-AJ.yaml`
  - PASS
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-FE-PRIVATE-COMPAT-EMITTER-SHRINK-RECHECK-SCREEN-AJ.yaml docs/audit/fe_private_compat_emitter_shrink_recheck_screen_aj_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`
  - PASS

## Decision

- screen complete
- strongest bounded statement after the latest emitter shrink recheck:
  - entry-surface private compat emitters are no longer the dominant residual
    issue
  - router registration and sceneRegistry compat prefix recognition are now the
    dominant remaining private compat baseline
