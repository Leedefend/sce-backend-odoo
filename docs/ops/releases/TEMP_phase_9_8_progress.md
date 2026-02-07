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

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T051349`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_guard.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-scene-warnings/20260207T052709`
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.portal.scene_warnings_limit.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-scene-warnings/20260207T052724`
- No other tests executed in this step.

## Notes
- This change is safe and additive: it only enables scene_key inference from action_xmlid when action_id mapping is missing.
- Recommended next step when Docker is available:
  - `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`
