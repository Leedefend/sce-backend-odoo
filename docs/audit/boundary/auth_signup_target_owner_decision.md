# auth_signup Target Owner Decision (ITER-2026-04-05-1036)

## Inputs

- `docs/audit/boundary/auth_signup_boundary_screen.md`
- `docs/audit/boundary/auth_signup_ownership_design_plan.md`
- `docs/audit/boundary/auth_signup_dependency_map.md`

## Decision

1. **Target owner (final)**: dedicated platform auth ownership line (platform-side auth module / auth governance domain), not industry module.
2. **Current owner (interim)**: `smart_construction_core` remains temporary owner until bounded implement batches complete.
3. **Chain boundary**: auth lifecycle migration remains isolated from `/api/*` runtime-shell chain.

## Rationale

- auth lifecycle semantics are cross-domain reusable (signup/activation/rate-limit/captcha policy).
- dependency evidence shows no scene/capability/ops/pack coupling.
- risk is public exposure continuity (`P1`), so compatibility-first migration is required.

## Compatibility Contract (Must Hold)

- route stability:
  - `/web/signup`
  - `/sc/auth/activate/<string:token>`
- config continuity:
  - all `sc.signup.*` keys remain recognized during transition.
- UX anchor continuity:
  - login page signup entry remains valid.
  - activation email link format remains valid.

## Implementation Gate For Next Batch

Before any code move:

1. select concrete target module path in a dedicated task contract;
2. define adapter strategy (source route delegation or preserved compatibility shim);
3. define auth-flow verification command set and rollback path.

## Risk Classification

- governance decision risk: low
- downstream implementation risk: `P1` (public auth lifecycle continuity)

## Next Suggestion

- open next dedicated implement-prep task:
  - produce concrete migration touch-list (controllers/views/hooks/models)
  - choose one of two paths:
    - route delegation shim first;
    - ownership contract hardening in place (if move is not yet safe).
