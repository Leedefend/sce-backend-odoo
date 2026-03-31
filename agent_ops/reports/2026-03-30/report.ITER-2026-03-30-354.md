# ITER-2026-03-30-354 Report

## Summary

- Migrated active runtime scene hooks out of [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_core/core_extension.py) into the scene layer module.
- Added a new scene-side hook owner at [core_extension.py](/mnt/e/sc-backend-odoo/addons/smart_construction_scene/core_extension.py) and exported it from [__init__.py](/mnt/e/sc-backend-odoo/addons/smart_construction_scene/__init__.py).
- Updated [sc_extension_params.xml](/mnt/e/sc-backend-odoo/addons/smart_construction_core/data/sc_extension_params.xml) so `smart_construction_scene` now precedes `smart_construction_core` in `sc.core.extension_modules`.
- Removed scene-oriented hook exports and `role_surface_override_provider` emission from the industry core module.

## Changed Files

- `addons/smart_construction_scene/core_extension.py`
- `addons/smart_construction_scene/__init__.py`
- `addons/smart_construction_core/data/sc_extension_params.xml`
- `addons/smart_construction_core/__init__.py`
- `addons/smart_construction_core/core_extension.py`
- `agent_ops/tasks/ITER-2026-03-30-354.yaml`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-354.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-354.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_core/core_extension.py addons/smart_construction_core/__init__.py addons/smart_construction_scene/core_extension.py addons/smart_construction_scene/__init__.py` -> PASS
- `python3 -m unittest discover -s addons/smart_core/tests -p 'test_scene_delivery_policy*_helper.py'` -> PASS
- `make verify.smart_core` -> PASS
- `rg -n "def smart_core_identity_profile|def smart_core_nav_scene_maps|def smart_core_surface_nav_allowlist|def smart_core_surface_deep_link_allowlist|def smart_core_surface_policy_default_name|def smart_core_surface_policy_file_default|def smart_core_critical_scene_target_overrides|def smart_core_critical_scene_target_route_overrides|role_surface_override_provider" addons/smart_construction_core/core_extension.py` -> PASS (no matches)

## Boundary Result

- Scene-layer ownership now includes:
  - `smart_core_identity_profile`
  - `smart_core_nav_scene_maps`
  - surface allowlists and default policy hooks
  - critical scene target override hooks
  - scene-oriented `role_surface_override_provider`

- Industry core ownership now keeps:
  - business facts
  - capability facts
  - server-action window mapping
  - non-scene business extension facts

## Risk Analysis

- Risk level was medium because this batch changed active runtime hook ownership.
- The migration remained controlled because:
  - extension-module order was updated explicitly
  - the new scene-side module exports a no-op `smart_core_register`, avoiding extension-loader warnings
  - core-side scene hook outputs were actually removed instead of leaving double ownership
- Residual cleanup still remains in `smart_construction_core/core_extension.py` for scene-oriented constants only if any inert documentation leftovers remain, but active ownership has been migrated.

## Rollback

- `git restore addons/smart_construction_scene/core_extension.py`
- `git restore addons/smart_construction_scene/__init__.py`
- `git restore addons/smart_construction_core/data/sc_extension_params.xml`
- `git restore addons/smart_construction_core/__init__.py`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore agent_ops/tasks/ITER-2026-03-30-354.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-354.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-354.json`

## Next Suggestion

- Continue scanning `smart_construction_core` for remaining scene-oriented inert metadata and move any still-active orchestration semantics into `smart_construction_scene`.
- After that, the next product-facing batch can safely work on scene publication and custom frontend fulfillment without re-opening the fact-layer boundary.
