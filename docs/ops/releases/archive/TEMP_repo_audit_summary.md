# Repo Audit Summary (Pre-Release)

Date: 2026-02-07
Branch: `main`
Worktree: clean (`git status -sb`)

## Snapshot
- Recent merges (last 5 commits):
  - `a4c2357` fix: harden scene target routing and portal url action flow (#286)
  - `f6f2fd5` fix(scene): harden core scene targets and upgrade legacy fallback (#285)
  - `03970af` fix(scene): preserve server targets and guard core scene fallback (#284)
  - `532d28b` release(r0): close nav semantics and first-login path (#283)
  - `2519087` feat(scene): add package installation registry and installed facts intent (#282)
- Core platform: Odoo 17 stack with custom Smart Core intent bus + Scene orchestration + Portal shell.

## Top-Level Modules (addons)
- `smart_core` (v17.0.1.0): intent dispatcher, contract system, action/menu/scene resolution.
- `smart_construction_core` (v17.0.0.3): domain models, lifecycle, dashboards, capability gates.
- `smart_construction_scene` (v17.0.0.1): scene orchestration and registry.
- `smart_construction_portal` (v17.0.1.0): portal pages + assets (lifecycle, capability matrix, dashboard).
- `smart_construction_seed` (v17.0.0.1.0): seed data (depends on bootstrap/core/account).
- `smart_construction_demo` (v0.2.0): demo data.
- `smart_construction_bootstrap` (v17.0.0.1.0): bootstrap base.
- `smart_construction_custom` (v17.0.1.0): project customizations.
- `sc_norm_engine` (v17.0.1.0.0): regional norm engine.

## Frontend (Portal Shell)
- App: `frontend/apps/web` (Vite).
- Auth: JWT via `Authorization: Bearer` (token-based), now explicitly avoids cookie auth for API requests.
- Key views:
  - `ActionView.vue` (action resolution, act_url handling, portal bridge logic).
  - `SceneView.vue` (scene -> target routing).
  - `WorkbenchView.vue` (fallback + diagnostics panel).
- Frontend API base: `VITE_API_BASE_URL` (example in `frontend/.env.example`).

## Portal (Odoo-side pages)
- Routes: `/portal/lifecycle`, `/portal/capability-matrix`, `/portal/dashboard`.
- Bridge route: `/portal/bridge` for shell token -> Odoo session handoff.
- Token propagation: `st` query param injected into portal page/API calls.

## Scene & Navigation
- Menu resolver now avoids directory->workbench by auto-redirect to first resolvable child.
- Scene targets upgraded at runtime when legacy fallback exists.
- Scene resolver accepts `action_id`, `menu_id`, `route`, `model` as valid targets.
- Workbench is treated as exception page only.

## Testing & Verification
- Available make targets (examples): `make verify.*`, `make fe.dev`, `make verify.frontend.build`.
- Smoke scripts updated:
  - `scripts/verify/fe_scene_target_smoke.js`
  - `scripts/verify/fe_scene_default_sort_smoke.js`
  - `scripts/verify/fe_scene_list_profile_smoke.js`
- Not run in this audit: end-to-end tests, container verify flows.

## Ops / Runbook / Release Docs
- Release workflows and templates in `docs/ops/releases/`.
- Execution allowlist and operational constraints in `docs/ops/codex_execution_allowlist.md`.
- Release SOP: `docs/ops/release_sop.md`.
- UX checklists: `docs/ops/ux/`.

## Environment & Compose
- `ENV` variants in `.env*`:
  - `.env` uses `ENV=local`
  - `.env.dev` -> `ENV=dev`
  - `.env.test` -> `ENV=test`
  - `.env.prod` -> `ENV=prod`
- DB filter is templated: `config/odoo.conf.template` uses `ODOO_DBFILTER`.
- Compose: `docker-compose.yml` for dev stack.

## Known Fragile Areas / Risks
- Portal bridge relies on session token binding; invalid/old cookies can still cause auth anomalies.
- act_url handling relies on target URLs; ensure portal routes remain stable.
- Cross-origin requests require clean browser state; token-based API auth should be preferred.

## Suggested Pre-Release Checklist (targeted)
1. Run critical smokes:
   - `make verify.portal.scene_list_profile_smoke.container`
   - `make verify.portal.scene_default_sort_smoke.container`
   - `make verify.frontend.build`
2. UI path sanity:
   - Login -> `projects.list` (default route)
   - Menu directory -> first actionable child
   - Core scenes: `projects.list`, `projects.ledger`, `projects.intake` openable
3. Portal bridge sanity:
   - Clicking lifecycle menu should open portal without secondary login

## Remote PR Reference (Context)

PR #269 (`Leedefend/sce-backend-odoo`):
- Title: `Portal v0.9.5: scene list profile + default sort for projects.list`
- Scope: scene defaults + list profile for `projects.list`, aligned defaults for `projects.list`/`projects.ledger`, and expanded scene smokes.
- Summary of touched files (from `gh pr view`):
  - `addons/smart_construction_scene/data/sc_scene_orchestration.xml`
  - `addons/smart_construction_scene/scene_registry.py`
  - `scripts/verify/fe_scene_default_sort_smoke.js`
  - `scripts/verify/fe_scene_list_profile_smoke.js`

## Temporary Docs Generated During Release Work
- `docs/ops/releases/TEMP_ui_validation_guide_after_scene_fixes.md`
- `docs/ops/releases/TEMP_systematic_scene_target_audit_summary.md`
- `docs/ops/releases/TEMP_release_r0_execution_summary.md`
- `docs/ops/releases/release_r0_launch_package.md`

---
End of summary.
