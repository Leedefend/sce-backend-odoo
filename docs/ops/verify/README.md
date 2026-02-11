# Verification Entry Points

## Core Gates
- `make gate.full`
  - Default strict mode includes Phase 9.8 guards.
  - Use `SC_GATE_STRICT=0` to skip Phase 9.8 enforcement.
  - Use `SC_SCENE_OBS_STRICT=1` to additionally enforce strict scene observability evidence during gate runs.
  - Default gate path includes `verify.portal.scene_observability_gate_smoke.container` (structure + preflight smoke + smoke chain).
  - Contract preflight now runs baseline freeze guard by default (`BASELINE_FREEZE_ENFORCE=1`).

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

## Scene Observability Strict Mode
- Default smoke targets remain compatibility-friendly and may skip when governance/audit models are unavailable:
  - `make verify.portal.scene_observability_preflight.refresh.container DB_NAME=<name>`
  - `make verify.portal.scene_observability_preflight_smoke.container`
  - `make verify.portal.scene_observability_preflight.latest`
  - `make verify.portal.scene_governance_action_smoke.container`
  - `make verify.portal.scene_auto_degrade_smoke.container`
  - `make verify.portal.scene_auto_degrade_notify_smoke.container`
  - `make verify.portal.scene_package_import_smoke.container`
  - Aggregate:
    - `make verify.portal.scene_observability_smoke.container`
- Strict variants enforce governance/audit artifacts and fail fast when evidence is missing:
  - `make verify.portal.scene_observability.structure_guard`
  - Baseline update:
    - `make verify.portal.scene_observability.structure_guard.update`
  - `make verify.portal.scene_observability_preflight.container` (`SCENE_OBSERVABILITY_PREFLIGHT_STRICT=1`)
  - `make verify.portal.scene_observability_preflight.report.strict`
  - `make verify.portal.scene_governance_action_strict.container`
  - `make verify.portal.scene_auto_degrade_strict.container`
  - `make verify.portal.scene_auto_degrade_notify_strict.container`
  - `make verify.portal.scene_package_import_strict.container`
- One-command strict aggregate:
  - `make verify.portal.scene_observability_strict.container`
- Gate-friendly smoke aggregate (structure guard + preflight smoke + smoke chain):
  - `make verify.portal.scene_observability_gate_smoke.container`
- UI semantic suite strict variant:
  - `make verify.portal.ui.v0_8.semantic.strict.container`

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
- One-command aggregate
  - `make verify.baseline.all` (platform + business)
  - `make gate.baseline.all` (platform gate + business gate)

## Business Increment Preflight
- Readiness report (non-blocking):
  - `make verify.business.increment.readiness`
- Readiness report (blocking):
  - `make verify.business.increment.readiness.strict`
- One-command preflight (refresh catalogs + scene shape + intent surface + readiness):
  - `make verify.business.increment.preflight`
- Strict preflight:
  - `make verify.business.increment.preflight.strict`

## Notes
- Typical env: `DB_NAME=sc_demo E2E_LOGIN=svc_e2e_smoke E2E_PASSWORD=demo`.
- Phase 9.8 warnings baseline can be adjusted via `SC_WARN_ACT_URL_LEGACY_MAX`.
- Menu exemptions file: `docs/ops/verify/menu_scene_exemptions.yml`.
- Strict failure guide: `docs/ops/verify/scene_observability_troubleshooting.md`.
- Baseline freeze guard:
  - `make verify.baseline.freeze_guard`
  - Temporary bypass in approved exception PR only:
    - `BASELINE_FREEZE_ALLOW=1 make verify.baseline.freeze_guard`
