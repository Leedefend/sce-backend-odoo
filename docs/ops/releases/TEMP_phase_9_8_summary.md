# TEMP Phase 9.8 Summary

## Scope
- Harden menu → scene coverage and act_url guardrails.

## Key Changes
- Scene key injection now falls back to `action_xmlid` when `action_id` mapping is unavailable.
- act_url menus without scene mapping emit `ACT_URL_MISSING_SCENE` warning.
- Warnings guard emits artifacts and enforces:
  - `ACT_URL_MISSING_SCENE` must be 0.
  - `ACT_URL_LEGACY` capped at 3 (baseline).
- Menu scene resolve smoke emits coverage summary and is appended to gate summary.
- Ensure demo/test loads admin config after groups and include `smart_core` dependency.
- Ensure `/api/v1/intent` routes are loaded in container by setting `server_wide_modules`.
- Menu scene resolve smoke now passes DB via query/header and logs error bodies.
- Demo data no longer hard-sets company currency; CNY remains active.

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`: PASS
  - `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T061808`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`: PASS
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T061815`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`: PASS
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T061818`
- `CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make gate.full`: PASS

## Files Touched
- `addons/smart_core/handlers/system_init.py`
- `scripts/verify/fe_menu_scene_resolve_smoke.js`
- `scripts/verify/fe_scene_diagnostics_smoke.js`
- `scripts/verify/scene_warnings_guard_summary.js`
- `scripts/verify/menu_scene_resolve_summary.js`
- `scripts/audit/scene_config_audit.js`
- `Makefile`
- `addons/smart_construction_core/__manifest__.py`
- `config/odoo.conf.template`
- `addons/smart_construction_demo/data/demo/demo_company_currency.xml`
- `docs/ops/releases/act_url_remaining_audit.md`
- `docs/ops/releases/TEMP_phase_9_8_progress.md`
- `docs/ops/releases/TEMP_phase_9_8_pr_body.md`

## Notes
- Gate enforcement now includes menu scene resolve, warnings guard, and legacy count cap.
- This phase is additive and focused on coverage + diagnostics, not functional feature change.
