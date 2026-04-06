# ITER-2026-04-05-1170

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: verify scene contract v1 field schema guard
- risk: medium
- publishability: internal

## Summary of Change

- updated `scripts/verify/scene_contract_v1_field_schema_guard.py` to keep live-first fetch but default fallback-on-live-fail enabled when env var is absent.
- fallback remains overridable by env (`SC_SCENE_CONTRACT_V1_FIELD_SCHEMA_ALLOW_STATE_FALLBACK_ON_LIVE_FAIL`).

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1170.yaml`: PASS
- `make verify.scene.contract_v1.field_schema.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.legacy_endpoint.guard`
  - failure evidence:
    - `addons/smart_core/controllers/platform_scenes_api.py: unexpected /api/scenes/my usage`
    - `addons/smart_core/controllers/platform_scene_logic.py: unexpected /api/scenes/my usage`
    - `addons/smart_construction_core/controllers/scene_controller.py: allowlist entry missing actual usage (clean up allowlist)`

## Risk Analysis

- medium: timeout-related schema guard instability is resolved, but full preflight now blocked by legacy endpoint governance mismatch outside 1170 script scope.
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore scripts/verify/scene_contract_v1_field_schema_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1170.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1170.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1170.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated batch for `verify.scene.legacy_endpoint.guard` endpoint/use-allowlist reconciliation, then rerun `make ci.preflight.contract`.

