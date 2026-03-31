# ITER-2026-03-30-360 Report

## Summary

- Removed the leftover definition-time scene placeholder parameter from `capability_registry`.
- Kept capability definitions purely business-oriented while leaving all scene binding ownership in `smart_construction_scene.services.capability_scene_targets`.
- Preserved capability payload behavior and ordering while finishing the remaining low-risk cleanup slice from the capability definition table.

## Changed Files

- `addons/smart_construction_core/services/capability_registry.py`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-360.md`
- `agent_ops/state/task_results/ITER-2026-03-30-360.json`
- `agent_ops/tasks/ITER-2026-03-30-361.yaml`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-360.yaml` -> PASS
- `python3 -m py_compile addons/smart_construction_core/services/capability_registry.py addons/smart_construction_scene/services/capability_scene_targets.py` -> PASS
- `make verify.smart_core` -> PASS

## Risk Analysis

- Risk remains low because the batch was a mechanical definition cleanup after the scene-binding runtime path had already been moved to the scene layer.
- User-visible capability payloads keep the same shape because `entry_target` and `default_payload` are still emitted through the scene-layer resolver.
- The remaining residual topic is no longer user-facing payload pollution; it is the telemetry-only `scene_key` dimension usage that needs a governance decision.

## Rollback

- `git restore addons/smart_construction_core/services/capability_registry.py`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-360.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-360.json`
- `git restore agent_ops/tasks/ITER-2026-03-30-361.yaml`

## Next Suggestion

- Start the next audit slice on `P4` telemetry-only scene dimensions:
  - classify which `scene_key` usages are pure analytics dimensions
  - decide which should remain as telemetry and which still leak into user-facing contracts
