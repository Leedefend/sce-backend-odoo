# TEMP Phase 9.8 Progress

## Scope
- Phase 9.8: menu → scene coverage hardening (act_url cleanup + resolve coverage).

## Changes
- Added action_xmlid fallback in menu scene key injection to avoid missing scene_key when action_id resolution is unavailable.
  - File: addons/smart_core/handlers/system_init.py
  - Logic: after action_id mapping, map meta.action_xmlid → scene_key via action_xmlid_map.

## Verification
- `make verify.menu.scene_resolve.container`:
  - Blocked in this environment: Docker socket permission denied.
  - Notes: running without `E2E_LOGIN/E2E_PASSWORD` defaults to demo_pm/demo, but login cannot be validated due to container restriction.
- No other tests executed in this step.

## Notes
- This change is safe and additive: it only enables scene_key inference from action_xmlid when action_id mapping is missing.
- Recommended next step when Docker is available:
  - `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo make verify.menu.scene_resolve.container`
