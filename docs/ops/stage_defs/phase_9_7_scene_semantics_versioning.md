# Phase 9.7 — Scene Semantics Coverage + Versioning v2

## Scope
- Add scene schema v2 and profiles v2 (compat with v1).
- Add semantic coverage smokes for tiles/targets/filters.
- Add versioning smoke enforcing schema_version + scene_version.
- Wire selected smokes into v0.8 semantic gate.

## New Files
- `addons/smart_construction_scene/schema/scene_schema_v2.json`
- `addons/smart_construction_scene/schema/scene_profiles_v2.json`
- `scripts/verify/lib/scene_schema_loader.js`
- `scripts/verify/lib/scene_schema_validator.js`
- `scripts/verify/fe_scene_tiles_semantic_smoke.js`
- `scripts/verify/fe_scene_targets_resolve_smoke.js`
- `scripts/verify/fe_scene_filters_semantic_smoke.js`
- `scripts/verify/fe_scene_versioning_smoke.js`

## Verification (system-bound)
```bash
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_tiles_semantic_smoke.container

DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_targets_resolve_smoke.container

DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_versioning_smoke.container
```

Optional (filters):
```bash
DB_NAME=sc_demo E2E_LOGIN=svc_project_ro E2E_PASSWORD='ChangeMe_123!' \
make verify.portal.scene_filters_semantic_smoke.container
```

## Gate Integration
- `verify.portal.ui.v0_8.semantic.container` now includes:
  - `verify.portal.scene_tiles_semantic_smoke.container`
  - `verify.portal.scene_targets_resolve_smoke.container`
  - `verify.portal.scene_versioning_smoke.container`

## Versioning Rules
- `schema_version` is required in `app.init`.
- `scene_version` is required in `app.init`.
- When `schema_version` = `v2`, v2 schema/profile are used.
- v1 remains loadable via loader for backward compatibility.

## Artifacts
Store the artifacts path from each smoke in PR body evidence.
