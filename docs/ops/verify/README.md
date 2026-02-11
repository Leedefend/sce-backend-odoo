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

## Phase D/E Cross-Stack Envelope Coverage
- `make verify.portal.envelope_smoke.container`
  - Aggregates:
    - `make verify.portal.scene_contract_smoke.container`
    - `make verify.portal.my_work_smoke.container`
    - `make verify.portal.execute_button_smoke.container`
    - `make verify.portal.cross_stack_contract_smoke.container`
  - Enforces intent envelope checks (`ok=true`) and `meta.trace_id` presence.

## Demo Baseline
- `make verify.demo`

## Baseline Semantics
- Platform baseline (environment/bootstrap consistency)
  - `make verify.platform_baseline`
  - `make gate.platform_baseline`
  - Legacy compatibility:
    - `make verify.baseline` (same as platform baseline)
    - `make gate.baseline` (same as platform baseline gate)
- Business baseline (core+seed install + business usable checks)
  - `make verify.business_baseline`
  - `make gate.business_baseline`
  - Legacy compatibility:
    - `make verify.p0.flow` (same as business baseline verification)

## Notes
- Typical env: `DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`.
- Phase 9.8 warnings baseline can be adjusted via `SC_WARN_ACT_URL_LEGACY_MAX`.
- Menu exemptions file: `docs/ops/verify/menu_scene_exemptions.yml`.
