# ITER-2026-03-31-397 Report

## Summary

- Audited the source of page mixing/drift with direct repository evidence.
- Limited the attribution target to two pages:
  - `projects.intake`
  - `project.management`
- Split the cause into two dimensions:
  - backend contract/runtime source
  - frontend realization source

## Changed Files

- `agent_ops/tasks/ITER-2026-03-31-397.yaml`
- `agent_ops/reports/2026-03-31/report.ITER-2026-03-31-397.md`
- `agent_ops/state/task_results/ITER-2026-03-31-397.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-31-397.yaml` -> PASS

## Attribution Basis

### 1. `projects.intake`

Backend fact evidence:

- `addons/smart_construction_scene/data/sc_scene_layout.xml:24`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:32`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:39`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:62`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:66`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:73`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:77`
- `addons/smart_construction_scene/data/sc_scene_layout.xml:108`

Observed backend shape:

- `projects.intake` is published as a `record/form` page.
- It explicitly declares `hero`, `form_main`, and `checklist` zones.
- It explicitly declares a `project.project` form profile.
- It explicitly declares `primary_fields` and `required_fields`.
- It explicitly declares `submit_action = project.initiation.enter`.

Additional business-entry evidence:

- `addons/smart_construction_core/handlers/project_initiation_enter.py:22`
- `addons/smart_construction_core/handlers/project_initiation_enter.py:32`
- `addons/smart_construction_core/handlers/project_initiation_enter.py:54`
- `addons/smart_construction_core/handlers/project_initiation_enter.py:117`

Observed entry behavior:

- the handler accepts a bounded set of project creation fields
- creates `project.project`
- returns a follow-up dashboard contract reference

Frontend realization evidence:

- `frontend/apps/web/src/views/ProjectsIntakeView.vue:2`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:8`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:10`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:23`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:97`
- `frontend/apps/web/src/views/ProjectsIntakeView.vue:110`

Observed frontend shape:

- the page renders two routing cards only:
  - `快速创建（推荐）`
  - `标准立项`
- `openQuickCreate()` routes to `/f/project.project/new`
- `openFullForm()` routes to `/a/:actionId`
- the custom page does not directly render the backend-declared hero/form/checklist structure
- the custom page does not directly render the declared primary field surface

Attribution:

- `projects.intake` drift is frontend-originated.
- The backend contract is form-shaped and field-shaped.
- The frontend realizes it as a routing shell.

### 2. `project.management`

Backend fact evidence:

- `addons/smart_construction_core/tests/test_project_dashboard_entry_backend.py:30`
- `addons/smart_construction_core/tests/test_project_dashboard_entry_backend.py:37`
- `addons/smart_construction_core/tests/test_project_dashboard_entry_backend.py:55`
- `addons/smart_construction_core/services/cost_tracking_service.py:12`
- `addons/smart_construction_core/services/cost_tracking_service.py:16`
- `addons/smart_construction_core/services/cost_tracking_service.py:151`
- `addons/smart_construction_core/services/payment_slice_service.py:12`
- `addons/smart_construction_core/services/payment_slice_service.py:16`
- `addons/smart_construction_core/services/payment_slice_service.py:145`

Observed backend shape:

- the project dashboard backend tests still assert a minimal entry carrier with blocks such as:
  - `progress`
  - `risks`
  - `next_actions`
- cost tracking is implemented as its own service with runtime block keys such as:
  - `cost_entry`
  - `cost_list`
  - `cost_summary`
- payment is implemented as its own service with runtime block keys such as:
  - `payment_entry`
  - `payment_list`
  - `payment_summary`

This means the backend exposes adjacent slice capabilities; it does not prove a single mixed monolithic page contract.

Frontend realization evidence:

- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:84`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:158`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:205`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:243`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:435`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:518`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:530`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:542`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:853`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:877`
- `frontend/apps/web/src/views/ProjectManagementDashboardView.vue:952`

Observed frontend shape:

- one page component iterates a shared `blockDescriptors` list
- the same component renders distinct slices behind conditional branches:
  - `cost_entry`
  - `payment_entry`
  - `settlement_summary`
- the same component keeps a `SCENE_ENTRY_INTENTS` map for:
  - `project.dashboard`
  - `project.execution`
  - `cost.tracking`
  - `payment`
  - `settlement`
- the same component changes summary rows and runtime refresh order by `currentSceneKey`

Attribution:

- `project.management` mixing is primarily frontend-originated.
- The backend provides adjacent scene/runtime capabilities.
- The frontend chooses to realize those adjacent capabilities inside one unified dashboard component.
- So the mixed experience is not best described as “the backend returned one intrinsically mixed page contract”.

## Per-Page Causal Conclusion

- `projects.intake`
  - backend contract/runtime mixing: `no`
  - frontend realization drift: `yes`
  - primary cause: `frontend`

- `project.management`
  - backend adjacent-slice capability surface: `yes`
  - backend single mixed page contract: `not proven`
  - frontend unified multi-scene realization: `yes`
  - primary cause of visible mixing: `frontend`

## Main Conclusion

The repository evidence does not support the claim that the visible mixing is
mainly caused by a single mixed backend page contract.

What the evidence supports is:

- `projects.intake` drift comes directly from frontend realization.
- `project.management` visible mixing comes mainly from frontend unification of
  multiple backend-adjacent capability slices into one page component.

So the dominant current source is frontend realization, not backend contract
pollution.

## Risk Analysis

- Risk remained low because this batch was audit-only.
- No product implementation files were modified.
- The main caution is interpretive:
  - backend does expose adjacent slices
  - but that is different from proving a single mixed backend page contract

## Rollback

- `git restore agent_ops/tasks/ITER-2026-03-31-397.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-31/report.ITER-2026-03-31-397.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-31-397.json`

## Next Suggestion

- If the next batch stays on alignment repair, target `projects.intake` first,
  because that page has the cleanest backend fact contract and the clearest
  frontend-caused drift.
