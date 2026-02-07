# Verification Entry Points

## Core Gates
- `make gate.full`
  - Default strict mode includes Phase 9.8 guards.
  - Use `SC_GATE_STRICT=0` to skip Phase 9.8 enforcement.

## Phase 9.8 Menu/Scene Coverage
- `make verify.menu.scene_resolve.container`
- `make verify.menu.scene_resolve.summary`
- `make verify.portal.scene_warnings_guard.container`
- `make verify.portal.scene_warnings_limit.container`
- `make verify.portal.act_url_missing_scene_report.container`
- `make verify.phase_9_8.gate_summary`

## Demo Baseline
- `make verify.demo`

## Notes
- Typical env: `DB_NAME=sc_demo E2E_LOGIN=demo_pm E2E_PASSWORD=demo`.
- Phase 9.8 warnings baseline can be adjusted via `SC_WARN_ACT_URL_LEGACY_MAX`.
