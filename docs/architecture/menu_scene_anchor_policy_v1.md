# Menu Scene Anchor Policy v1

## Goal

Keep business navigation scene-driven. Menu is an entry anchor, not a business action carrier.

## Hard Rules

1. Business menu nodes must resolve to `scene_key`.
2. Frontend menu click must prefer `scene_key` over `action_id`.
3. `action_id` remains fallback only for legacy nodes without scene mapping.
4. New business menu entries must register `menu_xmlid -> scene_key` mapping.
5. Scene mapping must point to a valid scene in scene registry.

## Runtime Order

1. menu node own `scene_key`
2. first descendant with `scene_key`
3. own `action_id` (legacy fallback)
4. first descendant with `action_id` (legacy fallback)

## Guarding

- `make verify.menu.scene_resolve`
- `node scripts/verify/fe_menu_no_action_smoke.js`
- `make verify.frontend.project_management.scene_bridge.guard`

