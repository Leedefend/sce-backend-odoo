# ITER-2026-04-05-1171

- status: FAIL
- mode: execute
- layer_target: Governance Monitoring
- module: legacy scene endpoint guard
- risk: medium
- publishability: internal

## Summary of Change

- aligned `scripts/verify/legacy_scene_endpoint_guard.py` allowlist with current real `/api/scenes/my` usage.
- added `addons/smart_core/controllers/platform_scenes_api.py` and `addons/smart_core/controllers/platform_scene_logic.py` to allowlist.
- removed stale allowlist entry `addons/smart_construction_core/controllers/scene_controller.py`.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1171.yaml`: PASS
- `make verify.scene.legacy_endpoint.guard`: PASS
- `make ci.preflight.contract`: FAIL
  - failure gate: `verify.scene.base_contract_asset_coverage.guard`
  - failure evidence:
    - `system_init missing nav_meta.ui_base_contract_asset_scene_count`
    - `system_init missing nav_meta.ui_base_contract_bound_scene_count`
    - `system_init missing nav_meta.ui_base_contract_missing_scene_count`

## Risk Analysis

- medium: legacy endpoint usage/allowlist mismatch is resolved, but preflight now blocked by system_init nav_meta asset coverage fields missing.
- repository stop rule triggered: required verify command failed.

## Rollback Suggestion

- `git restore scripts/verify/legacy_scene_endpoint_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1171.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1171.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1171.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- FAIL
- stop required by policy: yes
- unblock suggestion: open dedicated batch for `verify.scene.base_contract_asset_coverage.guard` by adding required `system_init.nav_meta` coverage fields, then rerun `make ci.preflight.contract`.

