# TEMP Phase 9.3–9.4 Progress

Date: 2026-02-07
Branch: `codex/phase-9-3-4`

## Phase 9.3 (act_url retirement + entry unification)

Completed:
- act_url audit classified (A-level direct scene mapping) in `docs/ops/releases/act_url_remaining_audit.md`.
- Legacy act_url deprecation warning added to system_init diagnostics.
- New menu → scene resolve smoke script and Make target:
  - `scripts/verify/fe_menu_scene_resolve_smoke.js`
  - `make verify.menu.scene_resolve`
  - `make verify.menu.scene_resolve.container`

Verification:
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve`:
  - FAIL (connect EPERM 127.0.0.1:8070; service not reachable)
- `E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`:
  - PASS (after preflight retry; artifacts: `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T045708`)

## Phase 9.4 (validation + evolution infrastructure)

Completed:
- E2E user contract draft: `docs/ops/verify/e2e_user_contract.md`
- Portal smoke credentials reference updated to include E2E contract
- Portal scenes tagged for migration readiness:
  - `portal_only: True`, `spa_ready: False` in `sc_scene_layout.xml`
- Scene config audit output extended with portal_only/spa_ready flags.

## Notes
- No new act_url entries introduced.
- Diagnostics now record legacy act_url via `ACT_URL_LEGACY` warning when resolved through scene_key.
- Host failure is environment-related (API service not reachable); container path is canonical and now PASS.
