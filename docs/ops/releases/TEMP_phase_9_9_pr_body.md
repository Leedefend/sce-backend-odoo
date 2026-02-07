## Summary
- Introduce canonical `svc_e2e_smoke` demo user for CI/gate smokes.
- Add menu → scene exemptions list and coverage accounting.
- Document scene governance and update verification entrypoints.

## Details
- Demo data adds `svc_e2e_smoke` with minimal read permissions.
- Menu scene resolve smoke now reads `docs/ops/verify/menu_scene_exemptions.yml` and reports exempt counts.
- Default smoke login for menu/scene diagnostics switched to `svc_e2e_smoke`.

## Verification
- Not run in this change set (docs/data update).
- Recommended:
  - `make demo.reset DB=sc_demo`
  - `DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full`

## Notes
- Exemptions file is empty by default; add entries only for non-actionable menus.
