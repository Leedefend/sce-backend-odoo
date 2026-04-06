# ITER-2026-04-05-1078

- status: PASS
- mode: implement
- layer_target: Industry Compatibility Cleanup
- module: smart_construction_core policy bridge legacy exports
- risk: low
- publishability: internal

## Summary of Change

- updated:
  - `agent_ops/tasks/ITER-2026-04-05-1078.yaml`
  - `addons/smart_construction_core/core_extension.py`
  - `addons/smart_construction_core/__init__.py`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1078.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1078.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed P1 policy legacy bridge exports from `core_extension.py`:
    - `smart_core_server_action_window_map`
    - `smart_core_file_upload_allowed_models`
    - `smart_core_file_download_allowed_models`
    - `smart_core_api_data_write_allowlist`
    - `smart_core_api_data_unlink_allowed_models`
    - `smart_core_model_code_mapping`
  - removed corresponding re-export entries from `smart_construction_core/__init__.py`.
  - retained `smart_core_create_field_fallbacks` compatibility export.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1078.yaml`: PASS
- `python3 -m py_compile addons/smart_construction_core/core_extension.py addons/smart_construction_core/__init__.py`: PASS
- `make verify.architecture.platform_policy_constant_owner_guard`: PASS

## Risk Analysis

- low: platform policy defaults layer already owns runtime policy path.
- residual: legacy capability/intent/system_init bridge exports remain for compatibility and should be cleaned in next bounded batches.

## Rollback Suggestion

- `git restore agent_ops/tasks/ITER-2026-04-05-1078.yaml`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore addons/smart_construction_core/__init__.py`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1078.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1078.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open bounded cleanup batch for P1 capability legacy exports.
