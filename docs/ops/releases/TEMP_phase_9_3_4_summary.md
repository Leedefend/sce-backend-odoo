# TEMP Phase 9.3–9.4 Summary

Date: 2026-02-07
Branch: `codex/phase-9-3-4`

## Phase 9.3 — act_url retirement + entry unification

### Delivered
- act_url remaining audit classified as legacy-only (A-level) in `docs/ops/releases/act_url_remaining_audit.md`.
- Legacy act_url deprecation warnings added to system_init diagnostics (`ACT_URL_LEGACY`).
- New menu → scene resolve smoke and Make target:
  - `scripts/verify/fe_menu_scene_resolve_smoke.js`
  - `make verify.menu.scene_resolve`
  - `make verify.menu.scene_resolve.container`

### Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve`:
  - FAIL (connect EPERM 127.0.0.1:8070; service not reachable)
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`:
  - FAIL (unresolved menus: menu_sc_root, menu_sc_dictionary, menu_sc_project_dashboard, menu_sc_project_dashboard_showcase)

## Phase 9.4 — validation + evolution infrastructure

### Delivered
- E2E user contract draft: `docs/ops/verify/e2e_user_contract.md`
- Portal smoke credentials updated to reference E2E contract.
- Portal scenes tagged with metadata for migration readiness:
  - `portal_only: True`, `spa_ready: False` in `addons/smart_construction_scene/data/sc_scene_layout.xml`
- Scene config audit output includes portal_only/spa_ready.

## Commits
- `2b652b9` feat(phase9.3): menu scene resolve + act_url warnings
- `356a4d1` docs(phase9.4): e2e contract + portal flags

## Notes
- No new act_url entries introduced; legacy-only policy documented.
- Host verification failure is environment-related; container failure indicates missing scene_key mappings pending env refresh.
