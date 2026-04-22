# BE Menu Tree Scene Map Supply Implement FB

## Goal

Consume the existing backend nav scene-map extension supply inside platform menu
controllers so menu interpretation no longer defaults to `scene_map={}` when the
backend already knows stable scene mappings.

## Verification

1. `python3 agent_ops/scripts/validate_task.py agent_ops/tasks/ITER-2026-04-21-BE-MENU-TREE-SCENE-MAP-SUPPLY-IMPLEMENT-FB.yaml`
2. `python3 addons/smart_core/tests/test_platform_menu_api_scene_map.py`
3. `git diff --check -- agent_ops/tasks/ITER-2026-04-21-BE-MENU-TREE-SCENE-MAP-SUPPLY-IMPLEMENT-FB.yaml addons/smart_core/controllers/platform_menu_api.py addons/smart_core/tests/test_platform_menu_api_scene_map.py docs/verify/be_menu_tree_scene_map_supply_implement_fb_v1.md docs/ops/iterations/delivery_context_switch_log_v1.md`

## Result

```json
{
  "result": "PASS",
  "closed_slice": "platform_menu_api default nav scene-map supply",
  "effect": [
    "/api/menu/tree now resolves extension-provided nav scene maps before menu target interpretation",
    "/api/menu/navigation now supplements caller-provided scene_map instead of requiring callers to fully supply it",
    "scene-known menu/action/model-view mappings can now resolve to scene targets without falling back to empty generic action interpretation"
  ],
  "residual_risk": "Unprovable generic action targets still remain compatibility-shaped until a later batch supplies stronger scene identity."
}
```
