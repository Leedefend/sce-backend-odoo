# auth_signup Implement-2 Feasibility (ITER-2026-04-05-1045)

## Constraint Check

- hard freeze active on:
  - `addons/**/__manifest__.py`
  - ACL/security domains (`security/**`, `record_rules/**`, `ir.model.access.csv`)

## Impact On Implement-2

### Not Feasible In Current Freeze
- physically moving `signup_throttle` model ownership across modules usually requires manifest dependency/load updates.
- moving signup default seed ownership across modules may require install hook wiring changes (manifest/hook ownership coupling).

### Feasible In Current Freeze
- in-place ownership hardening inside existing module boundary.
- bounded refactor that keeps model/hook files in current module and only improves delegation/documented ownership contract.
- verification-layer strengthening (smoke commands, compatibility checks).

## Decision

- Implement-2 should run as **in-place policy dependency hardening**, not cross-module relocation, under current freeze.
- cross-module dependency migration is deferred until a separately authorized manifest-change line exists.

## Suggested Next Batch

1. create implement task for in-place hardening scope only:
   - maintain `signup_throttle` and `_ensure_signup_defaults` behavior.
   - avoid manifest/ACL/security touch.
2. acceptance gate:
   - `py_compile` of touched files
   - `verify.frontend_api`
   - `scene_legacy_auth_smoke` with `E2E_BASE_URL`

## Risk Classification

- current feasible path risk: `P2` (bounded in-module hardening).
- deferred cross-module migration risk: `P1` until dedicated high-risk authorization line is opened.
