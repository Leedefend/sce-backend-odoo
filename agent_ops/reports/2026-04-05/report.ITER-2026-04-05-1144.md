# ITER-2026-04-05-1144

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: smart_core.capability_provider
- risk: medium
- publishability: internal

## Summary of Change

- added:
  - `agent_ops/tasks/ITER-2026-04-05-1144.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1144.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1144.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- updated:
  - `addons/smart_core/core/capability_provider.py`

## Platformization Outcome

- `CapabilityQueryService` is now the default runtime capability path.
- legacy fallback is now explicitly controlled by config toggle:
  - `smart_core.capability_legacy_fallback_enabled`
  - default behavior: disabled (`0`) means no fallback to legacy paths.
- when explicit fallback is enabled:
  - fallback is allowed for query exceptions or empty query results.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1144.yaml`: PASS
- `python3 -m py_compile addons/smart_core/core/capability_provider.py`: PASS
- marker grep checks (`capability_legacy_fallback_enabled`, `CapabilityQueryService`): PASS
- trusted capture check:
  - `artifacts/capability_payload_capture_1144/latest/capture_report.json`
  - result: `env_status=trusted`, `v1_count=6`, `v2_count=6`
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: default runtime path behavior changed to platform query service first without implicit legacy fallback.
- mitigation: explicit safety toggle remains available for controlled rollback behavior.

## Rollback Suggestion

- `git restore addons/smart_core/core/capability_provider.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1144.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1144.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1144.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next step suggestion: add dedicated guard that scans for unintended legacy fallback usage when toggle is disabled.
