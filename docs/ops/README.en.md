# Ops Documentation Entry

This directory hosts release, verification, and operational governance documentation.

## Primary Entry Points
- Release evidence directory: `docs/ops/releases/`
- Verification entry (including strict/compat modes): `docs/ops/verify/README.md`
- Baseline freeze policy: `docs/ops/baseline_freeze_policy.en.md`
- Scene observability command tiers:
  - preflight refresh: `make verify.portal.scene_observability_preflight.refresh.container DB_NAME=<name>`
  - preflight smoke: `make verify.portal.scene_observability_preflight_smoke.container`
  - preflight latest artifact: `make verify.portal.scene_observability_preflight.latest`
  - gate smoke aggregate: `make verify.portal.scene_observability_gate_smoke.container`
  - smoke aggregate: `make verify.portal.scene_observability_smoke.container`
  - strict aggregate: `make verify.portal.scene_observability_strict.container`
- Business increment preflight:
  - `make verify.business.increment.preflight`
  - `make verify.business.increment.preflight.strict`
  - optional profile: `BUSINESS_INCREMENT_PROFILE=base|strict`
- Phase 11 Backend Closure: `docs/ops/releases/current/phase_11_backend_closure.md`
- Phase 11.1 Contract Visibility: `docs/ops/releases/current/phase_11_1_contract_visibility.md`
- Temporary archive (non-official, traceability only): `docs/ops/releases/archive/temp/`

## Relation to Contract/Audit
- Contract hub: `docs/contract/README.md`
- Audit entry: `docs/audit/README.md`

## 双语
- 中文版: `docs/ops/README.md`
