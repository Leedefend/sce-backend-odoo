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

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`: PASS
  - `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T051349`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`: PASS
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T052709`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`: PASS
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T052724`

## Files Touched
- `addons/smart_core/handlers/system_init.py`
- `scripts/verify/fe_menu_scene_resolve_smoke.js`
- `scripts/verify/fe_scene_diagnostics_smoke.js`
- `scripts/verify/scene_warnings_guard_summary.js`
- `scripts/verify/menu_scene_resolve_summary.js`
- `scripts/audit/scene_config_audit.js`
- `Makefile`
- `docs/ops/releases/act_url_remaining_audit.md`
- `docs/ops/releases/TEMP_phase_9_8_progress.md`
- `docs/ops/releases/TEMP_phase_9_8_pr_body.md`

## Notes
- Gate enforcement now includes menu scene resolve, warnings guard, and legacy count cap.
- This phase is additive and focused on coverage + diagnostics, not functional feature change.
