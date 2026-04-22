# Non-Auth Dormant Cleanup Screen (ITER-2026-04-05-1051)

## Scope Snapshot

- active imports in `addons/smart_construction_core/controllers/__init__.py`:
  - `auth_signup`
  - `meta_controller`

Non-auth active runtime owner in this module import surface: none.

## Dormant Controller Surface (Non-Auth)

The following controller files still define historical `@http.route` but are not
imported by current controller init (thus not active owners in this module load
surface):

1. `addons/smart_construction_core/controllers/execute_controller.py`
2. `addons/smart_construction_core/controllers/frontend_api.py`
3. `addons/smart_construction_core/controllers/portal_execute_button_controller.py`
4. `addons/smart_construction_core/controllers/ui_contract_controller.py`

## Cleanup Candidate Classification

- candidate type A (doc/hygiene): mark these files as dormant-compat surfaces.
- candidate type B (code hygiene): bounded cleanup batch to remove/relocate dormant files only after double-checking smart_core owner parity.

## Recommended Next Batch

- low-risk screen/verify batch to assert owner parity matrix for the above four files, then open a pure cleanup implement batch (no behavior change).

## Risk Note

- do not delete dormant files directly in this batch.
- cleanup must remain non-functional and respect current platform owner routes.
