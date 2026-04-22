# Dormant Controller Cleanup Candidates

- checkpoint task: `ITER-2026-04-05-1031`
- scope: `addons/smart_construction_core/controllers`

## Method

1. read `controllers/__init__.py` import list
2. detect module files that still contain `@http.route`
3. compute `dormant = imported - active_route_modules`

## Current Active Route Modules

- `auth_signup`
- `meta_controller`

## Dormant Import Candidates

- `insight_controller`
- `capability_matrix_controller`
- `capability_catalog_controller`
- `scene_controller`
- `preference_controller`
- `scene_template_controller`
- `pack_controller`
- `ops_controller`
- `portal_dashboard_controller`

## Cleanup Suggestion

- safe first step: remove only dormant imports from `addons/smart_construction_core/controllers/__init__.py`.
- non-goal for this step: file deletion or service refactor.
