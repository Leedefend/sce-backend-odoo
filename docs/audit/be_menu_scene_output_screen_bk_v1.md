# BE Menu Scene Output Screen BK v1

## classification

```json
{
  "decision": "yes_backend_menu_must_be_scene_oriented",
  "current_state": "partially_aligned_but_not_fully_closed",
  "why": [
    "/api/menu/navigation is already the unified backend outlet for menu delivery",
    "formal menu contract already requires backend-generated route and active_match",
    "frontend still normalizes /native/action and resolves scene identity locally, which means the backend menu output has not fully closed over scene identity"
  ],
  "boundary_gap": [
    "menu delivery still allows frontend-side route reinterpretation",
    "menu nodes are not yet guaranteed to carry a directly consumable scene-oriented entry target"
  ],
  "frontend_requirement": "frontend menu consumer should stop inferring scene from native-action or compat-like route forms",
  "next_backend_need": "open a bounded backend screen or implement batch to materialize scene-oriented menu entry targets directly in nav_explained"
}
```

## evidence

- backend unified outlet:
  - [platform_menu_api.py](/mnt/e/sc-backend-odoo/addons/smart_core/controllers/platform_menu_api.py:136)
- backend convergence still delivers `nav_explained.tree/flat` as filtered backend output:
  - [menu_delivery_convergence_service.py](/mnt/e/sc-backend-odoo/addons/smart_core/delivery/menu_delivery_convergence_service.py:88)
- formal audit already freezes backend ownership of `route`, `active_match`, `reason_code`:
  - [menu_target_interpreter_audit_v1.md](/mnt/e/sc-backend-odoo/docs/menu/menu_target_interpreter_audit_v1.md:7)
- frontend still performs route reinterpretation on menu nodes:
  - [useNavigationMenu.ts](/mnt/e/sc-backend-odoo/frontend/apps/web/src/composables/useNavigationMenu.ts:28)

## decision

- menu delivery belongs to the same scene-oriented backend output boundary as other frontend-consumed contracts
- current menu contract is not fully closed yet because scene identity is still partially reconstructed on the frontend
- the next eligible move is backend-owned, not frontend-owned: either a dedicated backend screen to define the exact menu scene-entry shape, or a bounded implementation batch once that shape is frozen
