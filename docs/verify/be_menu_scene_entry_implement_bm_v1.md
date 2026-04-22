# BE Menu Scene Entry Implement BM v1

## scope

- add additive `entry_target` to `nav_explained` nodes
- preserve existing `route`, `target`, `target_type`, `delivery_mode`
- keep change bounded to backend menu interpreter and one focused unittest

## verification

- `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-20-BE-MENU-SCENE-ENTRY-IMPLEMENT-BM.yaml` → `PASS`
- `python3 addons/smart_core/tests/test_menu_target_interpreter_entry_target.py` → `PASS`
- `git diff --check -- agent_ops/tasks/ITER-2026-04-20-BE-MENU-SCENE-ENTRY-IMPLEMENT-BM.yaml docs/verify/be_menu_scene_entry_implement_bm_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md addons/smart_core/delivery/menu_target_interpreter_service.py addons/smart_core/tests/test_menu_target_interpreter_entry_target.py` → `PASS`

## implementation

- `MenuTargetInterpreterService` now adds additive `entry_target` on every explained menu node
- scene-resolved menu nodes emit formal scene entry payload:
  - `type: scene`
  - `scene_key`
  - `route`
  - `compatibility_refs`
  - `context`
- non-scene compatibility nodes emit bounded compatibility entry payload:
  - `type: compatibility`
  - `route`
  - `compatibility_refs`
- existing `route`, `target`, `target_type`, `delivery_mode`, and `active_match` remain unchanged for compatibility

## decision

```json
{
  "status": "PASS",
  "backend_menu_entry_target_materialized": true,
  "frontend_migration_readiness": "improved_but_not_yet_verified",
  "remaining_gap_to_check": "whether frontend menu consumer can now switch away from local /native/action reinterpretation",
  "backend_semantic_blocker": "none newly indicated by this batch"
}
```
