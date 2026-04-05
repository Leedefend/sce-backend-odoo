# ITER-2026-04-05-979

- status: FAIL
- mode: implement
- layer_target: Delivery Simulation Runtime Alignment
- module: scene module data-load consistency
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-979.yaml`
  - `addons/smart_construction_scene/data/sc_scene_layout.xml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-979.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-979.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - patched two scene version `scene_id` refs to existing IDs:
    - `sc_scene_project_initiation -> sc_scene_projects_intake`
    - `sc_scene_project_dashboard -> sc_scene_projects_dashboard`

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-979.yaml`: PASS
- `... make mod.install MODULE=smart_construction_scene DB_NAME=sc_prod_sim`: FAIL
  - new blocker after ref fix:
    - `null value in column "name" of relation "sc_scene" violates not-null constraint`
    - parse location: `smart_construction_scene/data/sc_scene_layout.xml:181`
  - root context: update record id `sc_scene_project_initiation` did not exist,
    causing create-with-partial-fields path.

## Risk Analysis

- medium: first-level XMLID mismatch fixed, but second-level update-target mismatch
  still blocks installation; publish decision remains blocked.

## Rollback Suggestion

- `git restore addons/smart_construction_scene/data/sc_scene_layout.xml`
- `git restore agent_ops/tasks/ITER-2026-04-05-979.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-979.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-979.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop_condition: `acceptance_failed`
- publishability: `blocked`

## Next Iteration Suggestion

- run follow-up source-fix batch to align `sc.scene` update record IDs with
  existing scene XMLIDs in the same file.
