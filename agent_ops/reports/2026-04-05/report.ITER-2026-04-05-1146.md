# ITER-2026-04-05-1146

- status: PASS
- mode: execute
- layer_target: Platform Layer
- module: smart_core extension and capability boundary
- risk: medium
- publishability: internal

## Summary of Change

- closed intent registry legacy path:
  - removed `smart_core_register` fallback from `addons/smart_core/core/extension_loader.py`
  - migrated all extension modules to `get_intent_handler_contributions` provider shape
- closed scene industry fallback path:
  - removed `call_extension_hook_first` fallback from scene handlers
  - fixed handlers to direct scene service path only
- closed policy constant ownership leakage:
  - removed platform policy constant definitions from `addons/smart_construction_core/core_extension.py`
  - kept only industry create fallback contribution payload (`INDUSTRY_CREATE_FIELD_FALLBACKS`)
- strengthened architecture guards:
  - `architecture_intent_registry_single_owner_guard` now checks loader + addon-wide legacy provider absence
  - `architecture_scene_bridge_industry_proxy_guard` now covers `scene_packages_installed`
  - `architecture_platform_policy_constant_owner_guard` now checks industry constant ownership absence

## Verification Result

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-05-1146.yaml`: PASS
- `python3 scripts/verify/architecture_intent_registry_single_owner_guard.py`: PASS
- `python3 scripts/verify/architecture_scene_bridge_industry_proxy_guard.py`: PASS
- `python3 scripts/verify/architecture_platform_policy_constant_owner_guard.py`: PASS
- `make verify.controller.boundary.guard`: PASS

## Risk Analysis

- medium: extension loader no longer accepts legacy registration hook; mitigated by same-batch migration of all existing `smart_core_register` providers to contribution providers.
- low runtime risk on scene path: handlers now require direct scene service import and no longer use extension fallback.

## Rollback Suggestion

- `git restore addons/smart_core/core/extension_loader.py`
- `git restore addons/smart_core/handlers/scene_package.py addons/smart_core/handlers/scene_governance.py addons/smart_core/handlers/scene_packages_installed.py`
- `git restore addons/smart_construction_core/core_extension.py`
- `git restore addons/smart_owner_core/core_extension.py addons/smart_construction_scene/core_extension.py`
- `git restore scripts/verify/architecture_intent_registry_single_owner_guard.py scripts/verify/architecture_scene_bridge_industry_proxy_guard.py scripts/verify/architecture_platform_policy_constant_owner_guard.py`

## Decision

- PASS
- next step suggestion: wire these three architecture guards into restricted baseline bundle for mandatory CI enforcement.
