# Pilot Feedback v0.1

## Scope
- Phase 15-B first pilot execution
- Database: `sc_demo`
- Operator path:
  - `project.initiation.enter`
  - `project.dashboard.enter`
  - `project.plan_bootstrap.enter`
  - `project.execution.enter`
  - `project.execution.advance`

## Run Summary
- Real pilot flow completed end-to-end.
- Execution state moved as expected:
  - `ready -> in_progress -> done`
- Runtime checks stayed aligned:
  - `pilot_precheck.overall_state=ready`
  - `execution_scope=single_open_task_only`
  - `task source=project.task`
  - `followup activity count=0 -> 1 -> 0`

## Feedback Classification

### Blocking
- None found in the controlled v0.1 pilot path after service health stabilized.

### Understanding
- High:
  - `EXECUTION_ALREADY_DONE` was surfaced by the real flow as the done-state blocked reason.
  - Risk:
    - if the frontend shows the raw code, non-developer operators do not know whether they need to retry, refresh, or stop.
  - Fix in Phase 15-B:
    - add friendly copy for done/ready/blocked/transition failure reason codes in `ProjectManagementDashboardView.vue`
- Medium:
  - `single_open_task_only` remains a strong semantic boundary and must still be explained in pilot onboarding.
  - Action:
    - keep it in frozen doc and operator guidance, but no new code path added.

### Experience
- Warmup noise:
  - immediately after `make restart`, the first verification attempt hit `Connection refused`.
  - Classification:
    - `ENV_UNSTABLE`, not a product blocker.
  - Action:
    - wait for container health before pilot execution evidence collection.

## Evidence
- `artifacts/backend/product_v0_1_pilot_execution_review.json`
- `artifacts/backend/product_v0_1_pilot_execution_review.md`
- `artifacts/backend/product_project_execution_state_smoke.json`
- `artifacts/backend/product_project_execution_advance_smoke.json`
- `artifacts/backend/product_project_execution_consistency_guard.json`
