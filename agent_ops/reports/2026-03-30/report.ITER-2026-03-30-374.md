# ITER-2026-03-30-374 Report

## Summary

- Moved the orchestration-oriented capability-group and capability seeds out of
  active core ownership and into scene-owned loading.
- Kept compatibility without manifest changes by using prefixed XMLIDs inside
  `smart_construction_scene`.
- Turned the old core seed files into compatibility shims so the existing core
  manifest can keep loading cleanly.

## Changed Files

- `addons/smart_construction_core/data/sc_capability_group_seed.xml`
- `addons/smart_construction_core/data/sc_scene_seed.xml`
- `addons/smart_construction_scene/data/sc_scene_orchestration.xml`
- `agent_ops/tasks/ITER-2026-03-30-374.yaml`
- `agent_ops/reports/2026-03-30/report.ITER-2026-03-30-374.md`
- `agent_ops/state/task_results/ITER-2026-03-30-374.json`
- `docs/ops/iterations/delivery_context_switch_log_v1.md`

## Verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-03-30-374.yaml` -> PASS
- `make mod.upgrade CODEX_NEED_UPGRADE=1 MODULE=smart_construction_scene DB_NAME=sc_demo` -> PASS
- `make verify.smart_core` -> PASS

## Migration Shape

- Added capability-group seeds to:
  - `smart_construction_scene/data/sc_scene_orchestration.xml`
- Added capability seeds to:
  - `smart_construction_scene/data/sc_scene_orchestration.xml`
- Used prefixed XMLIDs such as:
  - `smart_construction_core.sc_cap_group_project_management`
  - `smart_construction_core.sc_cap_project_work`

This keeps the external IDs stable while letting scene-owned data loading take
over the records.

- Replaced the old core files with compatibility shims:
  - `sc_capability_group_seed.xml`
  - `sc_scene_seed.xml`

## Boundary Outcome

- `smart_construction_core` no longer actively defines those orchestration
  seeds.
- `smart_construction_scene` now owns the load/update path for:
  - capability groups
  - capability seed records used by orchestration/runtime consumers

## Risk Analysis

- Risk remained low.
- No manifest, model, security, payment, settlement, or frontend files were touched.
- Compatibility was preserved through stable XMLIDs and no-op core stubs.

## Rollback

- `git restore addons/smart_construction_core/data/sc_capability_group_seed.xml`
- `git restore addons/smart_construction_core/data/sc_scene_seed.xml`
- `git restore addons/smart_construction_scene/data/sc_scene_orchestration.xml`
- `git restore agent_ops/tasks/ITER-2026-03-30-374.yaml`
- `git restore docs/ops/iterations/delivery_context_switch_log_v1.md`
- `git restore agent_ops/reports/2026-03-30/report.ITER-2026-03-30-374.md`
- `git restore agent_ops/state/task_results/ITER-2026-03-30-374.json`

## Next Suggestion

- Open one final audit on the remaining bootstrap-style files:
  - `sc_extension_params.xml`
  - `sc_extension_runtime_sync.xml`
  - `sc_subscription_default.xml`
  - `sc_cap_config_admin_user.xml`
- Decide whether they should stay in core or move to a more platform/governance-aligned owner.
