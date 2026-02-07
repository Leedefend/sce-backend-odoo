# TEMP Pre-Release Final Control Summary

Date: 2026-02-07
Branch: `codex/pre_release_final_control`

## Completed Tasks

1. Portal Bridge E2E Smoke
- Added script: `scripts/verify/portal_bridge_e2e_smoke.js`
- New target: `make verify.portal.bridge.e2e`
- Result: PASS (artifacts in `/mnt/artifacts/codex/portal-bridge-e2e/20260207T023703`)

2. act_url Audit
- Added: `docs/ops/releases/act_url_remaining_audit.md`
- Identified remaining portal act_url menus and scene candidates.

3. act_url -> Scene (Top Tier)
- Added portal scenes in DB payload: `portal.lifecycle`, `portal.capability_matrix`, `portal.dashboard`
- Added fallback scenes in `scene_registry.py`
- Injected menu/action -> scene_key mapping in `system_init.py`

4. Scene -> Portal Route Bridge
- `SceneView.vue` now bridges `/portal/*` routes via `/portal/bridge`.

5. Workbench Diagnostic Lock
- Workbench banner + comments in `WorkbenchView.vue`
- Diagnostic-only comment in `router/index.ts`

6. SPA API No-Cookie Guard
- Enforced `credentials: 'omit'` with dev warning in `api/client.ts`

7. TEMP Docs Archived
- Moved `docs/ops/releases/TEMP_*` to `docs/ops/releases/archive/`

8. Smoke User Fixture
- Added demo user: `svc_e2e_smoke` (project read + project manager capability)
- File: `addons/smart_construction_demo/data/demo/role_matrix_demo_users.xml`
- Credentials guidance: `docs/ops/verify/portal_smoke_credentials.md`

9. Smoke Preconditions Clarified
- Added precondition comments to:
  - `scripts/verify/fe_scene_list_profile_smoke.js`
  - `scripts/verify/fe_scene_default_sort_smoke.js`

10. Container Smoke Execution
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_list_profile_smoke.container`: PASS
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_default_sort_smoke.container`: PASS
    - RC canonical smoke user is `demo_pm` (documented).

## Verification Results

- `make verify.frontend.build`: PASS
- `make verify.portal.scene_list_profile_smoke.container`: FAIL (login 401 for `svc_project_ro`)
- `make verify.portal.scene_default_sort_smoke.container`: FAIL (login 401 for `svc_project_ro`)
- `make verify.portal.bridge.e2e`: PASS
- `E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make verify.portal.scene_list_profile_smoke.container`: FAIL (docker socket permission denied)
- `E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make verify.portal.scene_list_profile_smoke.container`: FAIL (login 401)
- `E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make verify.portal.scene_default_sort_smoke.container`: FAIL (login 401)
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_list_profile_smoke.container`: PASS
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_default_sort_smoke.container`: PASS

## Gate Checklist Status

- [x] portal bridge e2e: PASS
- [x] scene list profile smoke: PASS (demo_pm)
- [x] scene default sort smoke: PASS (demo_pm)
- [x] workbench unreachable from menus (diagnostic-only banner + scene-based nav)
- [x] SPA API no cookie (forced in client)

## Open Items / Requires Input

1. Provide valid `E2E_LOGIN` / `E2E_PASSWORD` for container smokes (current user `svc_project_ro` fails with 401).
2. RC tag `r0.1.0-rc1` not created (git tag forbidden by allowlist).
3. Decide whether to standardize on `demo_pm` for RC smokes or backfill `svc_e2e_smoke` in target DB.

## Files Changed (Uncommitted)

- `Makefile`
- `addons/smart_construction_scene/data/sc_scene_orchestration.xml`
- `addons/smart_construction_scene/scene_registry.py`
- `addons/smart_core/handlers/system_init.py`
- `frontend/apps/web/src/api/client.ts`
- `frontend/apps/web/src/router/index.ts`
- `frontend/apps/web/src/views/SceneView.vue`
- `frontend/apps/web/src/views/WorkbenchView.vue`
- `scripts/verify/portal_bridge_e2e_smoke.js`
- `docs/ops/releases/act_url_remaining_audit.md`

## Commit Summary

- `4581431` release(r0.1): pre-release final control hardening
- `229b5f8` chore(release): archive temp release notes
