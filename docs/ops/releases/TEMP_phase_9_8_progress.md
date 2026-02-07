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

## Verification
- `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`: PASS
  - Artifacts: `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T051349`
- No other tests executed in this step.

## Notes
- This change is safe and additive: it only enables scene_key inference from action_xmlid when action_id mapping is missing.
- Recommended next step when Docker is available:
  - `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`
