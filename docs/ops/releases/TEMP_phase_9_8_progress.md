# TEMP Phase 9.8 Progress

## Scope
- Phase 9.8: menu → scene coverage hardening (act_url cleanup + resolve coverage).

## Changes
- Added action_xmlid fallback in menu scene key injection to avoid missing scene_key when action_id resolution is unavailable.
  - File: addons/smart_core/handlers/system_init.py
  - Logic: after action_id mapping, map meta.action_xmlid → scene_key via action_xmlid_map.
- Added menu scene resolve smoke to gate.full for Phase 9.8 enforcement.
  - File: Makefile
  - Target: gate.full now runs verify.menu.scene_resolve.container
- Added diagnostic warning for act_url menus missing scene_key mapping.
  - File: addons/smart_core/handlers/system_init.py
  - Warning: ACT_URL_MISSING_SCENE
- Extended scene config audit to include normalize warning summary (act_url guard visibility).
  - File: scripts/audit/scene_config_audit.js
  - Output: scene_config_warnings.json (counts by warning code)
- Added warnings guard target to fail if ACT_URL_MISSING_SCENE is present (opt-in).
  - File: scripts/verify/fe_scene_diagnostics_smoke.js
  - Make target: verify.portal.scene_warnings_guard.container
- Enforced warnings guard in gate.full (Phase 9.8).
  - File: Makefile
- Added warnings guard summary artifact for gate audit.
  - File: scripts/verify/scene_warnings_guard_summary.js
  - Output: warnings.json / warnings_blocked.json
- Extended menu scene resolve smoke output to include coverage summary.
  - File: scripts/verify/fe_menu_scene_resolve_smoke.js
  - Output: menu_scene_resolve.json (summary + failures)
- Added gate summary extractor for menu scene resolve coverage.
  - File: scripts/verify/menu_scene_resolve_summary.js
  - Make target: verify.menu.scene_resolve.summary
- Added warnings limit guard to cap ACT_URL_LEGACY count (baseline=3).
  - File: scripts/verify/scene_warnings_guard_summary.js
  - Make target: verify.portal.scene_warnings_limit.container
- Prepared PR body template for Phase 9.8 submission.
  - File: docs/ops/releases/TEMP_phase_9_8_pr_body.md
- Added strict mode toggle for gate.full and explicit docker requirement message.
  - File: Makefile
  - Env: SC_GATE_STRICT=0 to skip 9.8 guards
- Baseline for ACT_URL_LEGACY now configurable via env.
  - File: scripts/verify/scene_warnings_guard_summary.js
  - Env: SC_WARN_ACT_URL_LEGACY_MAX (default 3)
- Added inferred scene_key guard when action_xmlid mapping is used.
  - File: addons/smart_core/handlers/system_init.py
  - Warning: SCENEKEY_INFERRED_NOT_FOUND
- Added Phase 9.8 gate summary index for release evidence.
  - File: scripts/verify/phase_9_8_gate_summary.js
  - Make target: verify.phase_9_8.gate_summary
- Added report output for ACT_URL_MISSING_SCENE with repair hints.
  - File: scripts/verify/act_url_missing_scene_report.js
  - Make target: verify.portal.act_url_missing_scene_report.container
- Ensured smart_construction_core demo/test loads admin config with valid groups.
  - File: addons/smart_construction_core/__manifest__.py
  - Change: load order adjusted to define groups before config data; added smart_core dependency.
- Ensured intent routes load in container for menu scene resolve smoke.
  - File: config/odoo.conf.template
  - Change: server_wide_modules now includes smart_core.
- Improved menu scene resolve smoke DB handling and error reporting.
  - File: scripts/verify/fe_menu_scene_resolve_smoke.js
  - Change: pass db via query + X-Odoo-DB header; log error bodies.
- Removed demo company currency hard-set to avoid journal conflict; keep CNY active.
  - File: addons/smart_construction_demo/data/demo/demo_company_currency.xml

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T061808`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-scene-warnings/20260207T061815`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-scene-warnings/20260207T061818`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.act_url_missing_scene_report.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-scene-warnings/20260207T061821`
- `CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make gate.full`: PASS
  - Includes: verify.demo, menu scene resolve, scene warnings guard/limit, act_url missing scene report.
  - Artifacts:
    - `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T061808`
    - `/mnt/artifacts/codex/portal-scene-warnings/20260207T061815`
    - `/mnt/artifacts/codex/portal-scene-warnings/20260207T061821`

## Notes
- Demo DB reset was required to apply currency seed changes before running gate.full.
