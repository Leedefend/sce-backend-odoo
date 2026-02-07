# TEMP Phase 9.9 Progress

## Scope
- Move CI/gate smokes off demo users by introducing canonical `svc_e2e_smoke`.
- Add menu → scene exemptions to avoid third-party noise.
- Document scene governance and verification entrypoints.

## Changes
- Added demo user `svc_e2e_smoke` with minimal read permissions.
  - File: addons/smart_construction_demo/data/scenario/s90_users_roles/10_users.xml
- Demo verify now expects `svc_e2e_smoke` to exist.
  - File: scripts/demo/verify.sh
- Default smoke login switched to `svc_e2e_smoke` in key gate scripts.
  - Files: scripts/verify/fe_menu_scene_resolve_smoke.js, scripts/verify/scene_warnings_guard_summary.js, scripts/audit/scene_config_audit.js
- Added menu exemptions file and logic in menu scene resolve smoke.
  - Files: docs/ops/verify/menu_scene_exemptions.yml, scripts/verify/fe_menu_scene_resolve_smoke.js
  - Summary now records exempt counts.
- Added governance and verification documentation.
  - Files: docs/architecture/scene_governance.md, docs/ops/verify/README.md
- Updated canonical smoke user documentation.
  - Files: docs/ops/verify/portal_smoke_credentials.md, docs/ops/verify/e2e_user_contract.md

## Verification
- Not run in this change set. Recommend:
  - `make demo.reset DB=sc_demo`
  - `DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full`

## Notes
- `menu_scene_exemptions.yml` is empty by default; add exemptions as needed.
