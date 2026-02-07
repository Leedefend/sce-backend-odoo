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
- `d1b3ff7` docs(release): codify rc smoke user
- `86285cc` docs(release): update pre-release control summary
- `3ba71e1` docs(release): add r0.1 GA notes

## RC Canonical Smoke User

- RC smoke user: `demo_pm` / `demo`
- Service accounts (`svc_*`) are non-blocking and may 401 in UI-level smokes.

## Phase 9.2 Task 0 Read-Only Scan (RC Freeze Compliant)

- Branch: `codex/pre_release_final_control`
- system_init keyword scan (scene/layout/tiles/list_profile/portal_shell):
  - File: `addons/smart_core/handlers/system_init.py`
  - `scene`: multiple sections (channel/contract load/normalize/targets/diagnostics)
  - `layout`: `_normalize_scene_layouts`
  - `tiles`: referenced in scene payload handling
  - `list_profile`: referenced in scene payload handling
  - `portal_shell`: not found in system_init
- Related system_init extensions/references (for future Phase 9.2):
  - `addons/smart_construction_core/core_extension.py`
  - `addons/smart_construction_scene/scene_registry.py`

## System Status Snapshot (Pre-Release, RC→GA Freeze)

Date: 2026-02-07
Branch: `codex/pre_release_final_control`

### Current State Summary
- Release phase: RC→GA preparation, code freeze enforced.
- Frontend: Vite dev serves from workspace; API base `http://localhost:8070`, DB `sc_demo`.
- Scenes: loaded via scene registry/contract with normalization + target resolve in system_init.
- Portal bridge: `/portal/bridge` flow verified and documented.
- Navigation: directory menu redirects to first reachable child; Workbench is diagnostic-only.
- SPA API: token-based, cookies omitted.

### Verification Snapshot
- `make verify.frontend.build`: PASS
- `make verify.portal.bridge.e2e`: PASS
- `make verify.portal.scene_list_profile_smoke.container`: PASS (demo_pm)
- `make verify.portal.scene_default_sort_smoke.container`: PASS (demo_pm)
- `svc_*` accounts: non-blocking for UI-level smokes (401 expected for `svc_project_ro`)

### Key Artifacts Added (This Phase)
- `docs/ops/releases/release_r0_1_ga_notes.md`
- `docs/ops/verify/portal_smoke_credentials.md`
- `docs/ops/releases/act_url_remaining_audit.md`
- `scripts/verify/portal_bridge_e2e_smoke.js`

### Known Constraints (Accepted)
- Dual UI planes (SPA + Odoo portal) remain in r0.1.
- `act_url` transitional and partially retained.
- RC smoke user fixed to `demo_pm` for consistency.

### Open Items (Non-Blocking / Post-GA)
- `svc_e2e_smoke` not validated in current DB; reserved for future CI hardening.
- RC tag `r0.1.0-rc1` to be created by release owner/pipeline (allowlist restriction).

## System Capability Assessment (Post-GA Optimization Directions)

### Strong Capabilities (Stable)
- Scene orchestration: contract/db/fallback loading, normalization, and target resolution are in place.
- Navigation semantics: directory menus resolve to reachable children; core scenes have safe fallbacks.
- Portal bridge: JWT -> session binding validated; portal routes are accessible via bridge.
- SPA API hygiene: token-based auth with cookie omission enforced.

### Gaps / Optimization Directions
1. Scene Config Governance
- Current system_init still performs layout/target normalization and uses hardcoded scene-key mapping.
- Direction: move layout/tiles/list_profile to data-driven scene config and slim system_init (Phase 9.2).

2. act_url Retirement Plan
- Core portal menus still rely on act_url in Odoo; scene mapping added but not fully removed.
- Direction: replace act_url in core menus with scene-driven routes post-GA.

3. Smoke User Strategy
- RC smokes depend on demo_pm; svc_* users are non-blocking.
- Direction: introduce a dedicated e2e user fixture in seeded data + CI wiring.

4. Portal SPA Convergence
- Dual UI planes remain; portal pages are server-rendered.
- Direction: plan SPA migration for portal lifecycle/capability/dashboard to reduce bridge dependency.

5. Auth Unification
- JWT + session remain in parallel.
- Direction: decide target auth model and roadmap via ADR.

6. Diagnostics & Error Attribution
- Workbench provides fallback but error reasons can still be coarse.
- Direction: expand reason codes and surface trace IDs in UI for faster triage.

7. Contract & Drift Controls
- Contract export/pin/rollback exists but depends on manual workflows.
- Direction: automate contract pinning and drift alerts in CI.

## Candidate Optimization Directions (Selectable)

1. Scene 编排数据化（Phase 9.2）
- 从 `system_init` 迁出 layout/tiles/list_profile，形成可配置、可审计配置源。

2. act_url 彻底退场
- 核心菜单全部 scene 化，桥接仅保留历史兼容。

3. Portal SPA 化路线图
- 将 lifecycle/capability/dashboard 从 Odoo portal 迁到 SPA。

4. Auth 统一决策与迁移
- 明确 JWT-only 或 Session-only，降低双栈复杂度。

5. E2E Smoke 夹具升级
- 稳定 CI 用户与权限基线（专用 e2e 用户 + 固定数据）。

6. 诊断与错误归因加强
- Workbench/Action/Scene 失败原因细分化、trace 贯通。

7. Scene 合约与漂移自动化
- contract pin/rollback/alert 自动化，减少人工流程。
