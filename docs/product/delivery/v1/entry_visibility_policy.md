# Entry Visibility Policy

## Objective
- Keep delivery roles focused on <=30 business-facing entries without deleting internal/debug paths.

## Policy
- delivery roles: only entries listed in `delivery_menu_tree_v1` are visible.
- internal/admin roles: can still access entries tagged `internal_only`.
- non-delivery entries are hidden by visibility tag, not removed.

## Hidden Entries (V1)
- cost.budget_alloc: internal_only
- scene_smoke_default: internal_only
