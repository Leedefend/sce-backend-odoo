# Entry Visibility Policy

## Objective
- Keep delivery roles focused on <=30 business-facing entries without deleting internal/debug paths.

## Policy
- delivery roles: only entries listed in `delivery_menu_tree_v1` are visible.
- internal/admin roles: can still access entries tagged `internal_only`.
- non-delivery entries are hidden by visibility tag, not removed.

## Mechanism
- scene tag field: `visibility_tags`
- delivery roles source: `docs/product/delivery/v1/role_package_source_v1.json:roles[].role_key`
- filter layer: `backend contract service (system.init/ui.contract response shaping)`
- frontend behavior: `frontend renders only filtered entries from contract payload`
- delivery role keys: executive, finance, ops, pm, purchase_manager

## Hidden Entries (V1)
- cost.budget_alloc: internal_only
- scene_smoke_default: internal_only
