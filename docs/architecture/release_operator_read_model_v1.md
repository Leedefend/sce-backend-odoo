# Release Operator Read Model v1

## Status

`release operator read model governed`

## Goal

Split mixed read assembly out of `release.operator.surface` into a stable, read-only, reusable model.

## Contract

- `contract_version`
- `identity`
- `products`
- `current_release_state`
- `pending_approval_queue`
- `candidate_snapshots`
- `release_history_summary`
- `available_operator_actions`

## Runtime Rules

- read model is read-only
- read model does not execute mutate flows
- surface and frontend page consume read model instead of rebuilding state locally
- legacy `release_operator_surface_v1` top-level keys remain for compatibility

## Layer Notes

- Layer Target: `Platform Layer / Delivery Runtime Layer / Frontend Layer`
- Module:
  - `addons/smart_core/delivery/release_operator_read_model_service.py`
  - `addons/smart_core/delivery/release_operator_surface_service.py`
  - `frontend/apps/web/src/views/ReleaseOperatorView.vue`
- Reason: stabilize operator reads as a reusable delivery read layer
