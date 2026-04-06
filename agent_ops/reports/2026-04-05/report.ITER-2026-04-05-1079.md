# ITER-2026-04-05-1079

- status: PASS
- mode: implement
- layer_target: Industry Compatibility Cleanup
- module: smart_construction_core capability hook exports
- risk: low
- publishability: internal

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-1079.yaml`
  - `addons/smart_construction_core/core_extension.py`
  - `addons/smart_construction_core/__init__.py`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1079.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1079.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed legacy capability hook names and switched to provider hooks:
    - added `get_capability_contributions(env, user)`
    - added `get_capability_group_contributions(env)`
    - removed legacy exports `smart_core_list_capabilities_for_user` and `smart_core_capability_groups`
  - updated module re-exports to provider hook names.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1079.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/core_extension.py addons/smart_construction_core/__init__.py`: PASS
- `make verify.architecture.capability_registry_platform_owner_guard`: PASS

## Risk Analysis

- low: platform loader already prefers provider hooks; behavior remains compatible.
- residual: legacy intent/system_init/create-fallback wrappers still remain for subsequent cleanup.

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-04-05-1079.yaml`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore addons/smart_construction_core/__init__.py`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1079.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1079.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open bounded cleanup batch for deprecated `smart_core_register` export removal.
