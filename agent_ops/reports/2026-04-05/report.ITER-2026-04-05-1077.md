# ITER-2026-04-05-1077

- status: PASS
- mode: implement
- layer_target: Industry Compatibility Cleanup
- module: smart_construction_core scene bridge legacy exports
- risk: low
- publishability: internal

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-1077.yaml`
  - `addons/smart_construction_core/core_extension.py`
  - `addons/smart_construction_core/__init__.py`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1077.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1077.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed P0 scene legacy bridge exports from industry module:
    - `smart_core_scene_package_service_class`
    - `smart_core_scene_governance_service_class`
    - `smart_core_load_scene_configs`
    - `smart_core_has_db_scenes`
    - `smart_core_get_scene_version`
    - `smart_core_get_schema_version`
  - removed corresponding re-export entries from `smart_construction_core/__init__.py`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1077.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/core_extension.py addons/smart_construction_core/__init__.py`: PASS
- `make verify.architecture.scene_bridge_industry_proxy_guard`: PASS

## Risk Analysis

- low: platform direct-connect path is already active and verified.
- residual: remaining legacy bridge exports (intent/capability/policy/system_init) still present and should be cleaned in subsequent bounded batches.

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-04-05-1077.yaml`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore addons/smart_construction_core/__init__.py`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1077.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1077.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open bounded cleanup batch for P1 legacy policy bridge exports.
