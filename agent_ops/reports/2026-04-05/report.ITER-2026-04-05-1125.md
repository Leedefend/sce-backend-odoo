# ITER-2026-04-05-1125

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: smart_core.scene_registry_provider
- risk: medium
- publishability: internal

## Summary of Change

- updated:
  - `addons/smart_core/core/scene_registry_provider.py`
  - `scripts/verify/architecture_scene_bridge_industry_proxy_guard.py`
  - `agent_ops/tasks/ITER-2026-04-05-1125.yaml`
  - `agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1125.md`
  - `agent_ops/state/task_results/ITER-2026-04-05-1125.json`
  - `docs/ops/iterations/delivery_context_switch_log_v1.md`
- implementation:
  - removed `smart_core_scene_*` and `call_extension_hook_first` fallback path from scene registry provider.
  - platform scene provider now uses direct `smart_construction_scene.scene_registry` access only.
  - strengthened scene bridge guard to fail if legacy fallback hooks reappear.

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1125.yaml`: PASS
- `python3 -m py_compile addons/smart_core/core/scene_registry_provider.py scripts/verify/architecture_scene_bridge_industry_proxy_guard.py`: PASS
- `rg -n "smart_core_load_scene_configs|smart_core_has_db_scenes|smart_core_get_scene_version|smart_core_get_schema_version|call_extension_hook_first" addons/smart_core/core/scene_registry_provider.py && exit 1 || exit 0`: PASS
- `python3 scripts/verify/architecture_scene_bridge_industry_proxy_guard.py`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: direct-only scene path removes compatibility fallback; environments lacking `smart_construction_scene.scene_registry` runtime would fail earlier.
- mitigated: current platform handlers already rely on direct scene package/governance services and related guard remains green.

## Rollback Suggestion

- `git restore addons/smart_core/core/scene_registry_provider.py`
- `git restore scripts/verify/architecture_scene_bridge_industry_proxy_guard.py`
- `git restore agent_ops/tasks/ITER-2026-04-05-1125.yaml`
- `git restore agent_ops/reports/2026-04-05/report.ITER-2026-04-05-1125.md`
- `git restore agent_ops/state/task_results/ITER-2026-04-05-1125.json`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`

## Decision

- PASS
- next stage suggestion: open Clause-4 implementation batch to retire legacy platform policy smart_core_* compatibility hooks.
