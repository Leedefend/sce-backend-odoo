# auth_signup Implement-2 Plan (ITER-2026-04-05-1044)

## Objective

- align policy dependencies after controller ownership handoff.
- scope to throttle model + signup default seed ownership path.

## Planned Scope

### Candidate Files
- `addons/smart_construction_core/models/support/signup_throttle.py`
- `addons/smart_construction_core/hooks.py` (`_ensure_signup_defaults` section)
- potential target module files under platform auth domain (to be fixed in implement task)

### Out of Scope
- `security/**`, `record_rules/**`, `ir.model.access.csv`, `__manifest__.py`
- payment/settlement/account domains
- frontend behavior changes

## Batch Strategy

1. **Screen**: confirm target owner for throttle/default-seed dependencies.
2. **Implement**: move or delegate dependencies with zero behavior drift.
3. **Verify**: rerun `verify.frontend_api` + `scene_legacy_auth_smoke` with corrected command contract.

## Acceptance Gate (Implement-2)

- `py_compile` for changed python files.
- `FRONTEND_API_BASE_URL=http://127.0.0.1:18069 ... make verify.frontend_api`
- `E2E_BASE_URL=http://127.0.0.1:18069 python3 scripts/verify/scene_legacy_auth_smoke.py`

## Stop Conditions

- any required ACL/manifest/security changes.
- inability to preserve `sc.signup.*` config behavior.
- duplicate ownership unresolved after dependency handoff.

## Rollback Baseline

- restore changed model/hook files and target auth dependency files.
- rerun auth smoke to verify rollback integrity.
