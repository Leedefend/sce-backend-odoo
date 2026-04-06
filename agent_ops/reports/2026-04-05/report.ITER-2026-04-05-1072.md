# ITER-2026-04-05-1072

- status: PASS
- mode: implement
- layer_target: Platform system.init Runtime
- module: ext_facts contribution collection and merge path
- risk: low
- publishability: internal

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-1072.yaml`
  - `addons/smart_core/core/system_init_extension_fact_merger.py`
  - `addons/smart_core/handlers/system_init.py`
  - `addons/smart_construction_core/core_extension.py`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1072.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1072.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - added platform-owned contribution collector:
    - `apply_extension_fact_contributions(data, env, user, context)`
  - wired `system.init` to execute contribution collection before legacy extension hook.
  - converted construction module to provider-first mode:
    - added `get_system_init_fact_contributions(env, user, context=None)`
    - kept `smart_core_extend_system_init` as compatibility wrapper only.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1072.yaml`: PASS
- `python3 -m py_compile addons/smart_core/core/system_init_extension_fact_merger.py addons/smart_core/handlers/system_init.py addons/smart_construction_core/core_extension.py`: PASS

## Risk Analysis

- low: migration keeps legacy hook compatibility while switching primary ownership path to platform merge.
- residual: other extension modules may still rely only on legacy hook until subsequent conversion batches.

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-04-05-1072.yaml`
- `git restore addons/smart_core/core/system_init_extension_fact_merger.py`
- `git restore addons/smart_core/handlers/system_init.py`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1072.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1072.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open scene direct-connect implementation batch (task 3.2) to remove smart_core_scene_* dependency path.
