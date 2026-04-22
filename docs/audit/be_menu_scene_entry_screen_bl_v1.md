# BE Menu Scene Entry Screen BL v1

## status

`PASS`

## classification

```json
{
  "required_backend_shape": {
    "public_primary_field": "entry_target",
    "minimum_fields": [
      "type",
      "scene_key",
      "route",
      "compatibility_refs",
      "context"
    ],
    "compatibility_refs_examples": [
      "menu_id",
      "action_id",
      "target_type",
      "delivery_mode"
    ]
  },
  "current_gap": [
    "nav_explained still exposes route as the primary navigable field",
    "target only carries scene_key or action payload, but not one formal scene-oriented entry contract",
    "frontend still normalizes native or compat-like route forms because scene identity is not fully materialized as one public entry shape"
  ],
  "implementation_rule": "additive_only_keep_existing_route_and_target_for_compat",
  "backend_semantic_blocker": "none"
}
```

## evidence

- `/api/menu/navigation` returns `nav_explained` from `MenuTargetInterpreterService` and filtered convergence output:
  - [platform_menu_api.py](/mnt/e/sc-backend-odoo/addons/smart_core/controllers/platform_menu_api.py:136)
- current interpreter still centers output on:
  - `target_type`
  - `delivery_mode`
  - `route`
  - `target`
  - [menu_target_interpreter_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/delivery/menu_target_interpreter_service.py:332)
- current route building still emits `/s/...`, `/a/...`, `/native/action/...` as navigation forms:
  - [menu_target_interpreter_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/delivery/menu_target_interpreter_service.py:282)
- frontend menu contract still only types `route` and generic `target`:
  - [navigation.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/types/navigation.ts:13)
- frontend menu consumer still reinterprets `/native/action/:id` locally:
  - [useNavigationMenu.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/composables/useNavigationMenu.ts:28)

## decision

- backend menu delivery must add one formal `entry_target` as the public scene-oriented entry surface
- `route` and `target` may remain temporarily as compatibility fields during migration
- next eligible batch is backend implementation, focused on adding additive `entry_target` to `nav_explained.tree/flat`
