# ITER-2026-04-05-1145

- status: PASS
- mode: execute
- layer_target: Governance Monitoring
- module: scripts/verify
- risk: low
- publishability: internal

## Summary of Change

- added:
  - `scripts/verify/architecture_capability_legacy_fallback_usage_guard.py`
  - `agent_ops/tasks/ITER-2026-04-05-1145.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1145.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1145.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Guard Coverage

- guard enforces default-path governance in `capability_provider.py`:
  - requires explicit helper `def _capability_legacy_fallback_enabled(...)`
  - requires config key `smart_core.capability_legacy_fallback_enabled`
  - forbids obsolete toggle `smart_core.capability_registry_query_v2_enabled`
  - requires `CapabilityQueryService` path in `load_capabilities_for_user`
  - requires no-fallback short-circuit conditions when legacy toggle is disabled

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1145.yaml`: PASS
- `python3 -m py_compile scripts/verify/architecture_capability_legacy_fallback_usage_guard.py`: PASS
- `python3 scripts/verify/architecture_capability_legacy_fallback_usage_guard.py`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- low: guard-only addition; no runtime behavior change.
- guard reduces regression risk after default-path promotion by failing on implicit legacy fallback drift.

## Rollback Suggestion

- `git restore scripts/verify/architecture_capability_legacy_fallback_usage_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1145.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1145.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1145.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next step suggestion: add this guard into restricted/architecture verify bundle for automatic CI enforcement.
