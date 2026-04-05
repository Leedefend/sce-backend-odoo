# ITER-2026-04-05-978

- status: FAIL
- mode: implement
- layer_target: Delivery Simulation Runtime Alignment
- module: scene installation dependency mapping
- risk: medium
- publishability: blocked

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-978.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-978.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-978.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - repaired missing core capability-group/capability/scene baseline mappings in runtime.
  - retried `smart_construction_scene` installation.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-978.yaml`: PASS
- runtime repair script (`odoo shell`) for missing `smart_construction_core.*` mappings: PASS
  - created baseline rows: `sc.capability.group=8`, `sc.capability=5`, `sc.scene=1`
- `... make mod.install MODULE=smart_construction_scene DB_NAME=sc_prod_sim`: FAIL
  - new blocker:
    - `External ID not found in the system: smart_construction_scene.sc_scene_project_initiation`
    - parse location: `smart_construction_scene/data/sc_scene_layout.xml:121`

## Risk Analysis

- medium: runtime dependency repair removed the first blocker, but module now fails
  on internal XML reference consistency, indicating source-data ordering/id drift.
  This cannot be safely solved by runtime-only patching.

## Rollback Suggestion

- keep runtime changes if further source-level fix batch is planned.
- or restore `sc_prod_sim` snapshot to revert runtime repair artifacts.
- repo rollback:
  - `git restore agent_ops/tasks/ITER-2026-04-05-978.yaml`
  - `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-978.md`
  - `git restore agent_ops/state/task_results/ITER-2026-04-05-978.json`
  - `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop_condition: `acceptance_failed`
- publishability: `blocked`

## Next Iteration Suggestion

- open dedicated source-fix batch for
  `addons/smart_construction_scene/data/sc_scene_layout.xml` and related scene
  IDs in `sc_scene_orchestration.xml`, then rerun installation + publish gates.
