## Summary
- Introduce canonical `svc_e2e_smoke` demo user for CI/gate smokes.
- Add menu → scene exemptions list and coverage accounting.
- Document scene governance and update verification entrypoints.

## Details
- Demo data adds `svc_e2e_smoke` with minimal read permissions.
- Menu scene resolve smoke now reads `docs/ops/verify/menu_scene_exemptions.yml` and reports exempt counts.
- Default smoke login for menu/scene diagnostics switched to `svc_e2e_smoke`.

## Verification
- `CODEX_MODE=gate make demo.reset DB=sc_demo`: PASS
- `CODEX_MODE=gate DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo make gate.full`: PASS
  - `/mnt/artifacts/codex/portal-menu-scene-resolve/20260207T064626`
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T064632`
  - `/mnt/artifacts/codex/portal-scene-warnings/20260207T064637`

## Notes
- Exemptions file is empty by default; add entries only for non-actionable menus.
