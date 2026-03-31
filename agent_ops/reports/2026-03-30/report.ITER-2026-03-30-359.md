# ITER-2026-03-30-359 Report

## Summary

- Moved capability entry-target scene binding into `smart_construction_scene` through a dedicated capability scene-target service.
- Switched `capability_registry` to resolve entry targets and payload routes from scene-layer bindings instead of building them from scene ownership logic embedded in core service helpers.
- Moved execution projection source-model scene binding into the scene layer, leaving `project_execution_item_projection_service` responsible only for business projection facts.

## Changed Files

- `addons/smart_construction_scene/services/capability_scene_targets.py`
- `addons/smart_construction_scene/services/__init__.py`
- `addons/smart_construction_core/services/capability_registry.py`
- `addons/smart_construction_core/services/project_execution_item_projection_service.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-359.md`
- `agent_ops/state/task_results/ITER-2026-03-30-359.json`
- `agent_ops/tasks/ITER-2026-03-30-360.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-359.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_core/services/capability_registry.py addons/smart_construction_core/services/project_execution_item_projection_service.py addons/smart_construction_scene/services/capability_scene_targets.py addons/smart_construction_scene/services/__init__.py` -> PASS
- `make verify.smart_core` -> PASS

## Risk Analysis

- Risk remains low because the batch preserved current emitted payload shape (`entry_target`, `default_payload`, `scene_key`) while changing who computes the scene semantics.
- `capability_registry` still retains a definition-time placeholder parameter carrying the old scene bindings; this no longer drives payload computation, but it is the next residual cleanup target.
- No ACL, manifest, or financial model paths were touched.

## Rollback

- `git restore addons/smart_construction_scene/services/capability_scene_targets.py`
- `git restore addons/smart_construction_scene/services/__init__.py`
- `git restore addons/smart_construction_core/services/capability_registry.py`
- `git restore addons/smart_construction_core/services/project_execution_item_projection_service.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-359.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-359.json`
- `git restore agent_ops/tasks/ITER-2026-03-30-360.yaml`

## Next Suggestion

- Continue with the next low-risk cleanup slice:
  - remove the leftover definition-time scene placeholder parameter from `capability_registry`
  - keep scene bindings only in `smart_construction_scene.services.capability_scene_targets`
