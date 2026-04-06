# ITER-2026-04-05-1126

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: smart_core.platform_policy_defaults
- risk: medium
- publishability: internal

## Summary of Change

- updated:
  - `addons/smart_core/core/platform_policy_defaults.py`
  - `scripts/verify/architecture_platform_policy_constant_owner_guard.py`
  - `agent_ops/tasks/ITER-2026-04-05-1126.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1126.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1126.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed legacy `smart_core_*` policy fallback hooks from platform policy defaults.
  - retained contribution hooks (`get_*_contributions`) as the only extension path.
  - strengthened policy owner guard to fail if any legacy `smart_core_*` policy fallback token appears.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1126.yaml`: PASS
- `python3 -m py_compile addons/smart_core/core/platform_policy_defaults.py scripts/verify/architecture_platform_policy_constant_owner_guard.py`: PASS
- `rg -n "smart_core_server_action_window_map|smart_core_file_upload_allowed_models|smart_core_file_download_allowed_models|smart_core_api_data_write_allowlist|smart_core_api_data_unlink_allowed_models|smart_core_model_code_mapping|smart_core_create_field_fallbacks" addons/smart_core/core/platform_policy_defaults.py && exit 1 || exit 0`: PASS
- `python3 scripts/verify/architecture_platform_policy_constant_owner_guard.py`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: modules still relying on legacy `smart_core_*` policy fallback exports no longer affect platform policy defaults.
- mitigated: contribution hooks remain available for supported extension path.

## Rollback Suggestion

- `git restore addons/smart_core/core/platform_policy_defaults.py`
- `git restore scripts/verify/architecture_platform_policy_constant_owner_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1126.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1126.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1126.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open Clause-5 implementation batch to remove legacy `smart_core_extend_system_init` hook execution path.
