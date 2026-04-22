# auth_signup Ownership Design Plan (ITER-2026-04-05-1034)

## Design Position

- source finding: `docs/audit/boundary/auth_signup_boundary_screen.md`
- decision: keep `auth_signup` out of `/api/*` runtime-shell migration chain.
- governance target: move to dedicated auth ownership line in bounded batches.

## Boundary Scope

### In Scope
- `/web/signup`
- `/sc/auth/activate/<string:token>`
- signup policy config keys (`sc.signup.*`) ownership mapping
- signup throttle and activation flow dependency inventory

### Out of Scope
- `security/**`
- `record_rules/**`
- `ir.model.access.csv`
- `__manifest__.py`
- payment/settlement/account domains

## Ownership Objective

1. keep auth lifecycle backend-owned (`business-fact layer`).
2. avoid frontend model-specific patching.
3. avoid mixing auth lifecycle migration with platform runtime API cleanup.

## Proposed Batch Chain

### Batch A (screen)
- objective: freeze full auth dependency map and touch-list.
- deliverable: `auth_signup_dependency_map.md` (new line item in future batch).
- acceptance: task contract validation + bounded evidence table.

### Batch B (screen)
- objective: decide target owner module (dedicated auth module vs current module with ownership contract).
- deliverable: `auth_signup_target_owner_decision.md`.
- acceptance: explicit owner + compatibility policy + rollback entry.

### Batch C (implement, low-risk)
- objective: route-shell relocation or ownership contract hardening (one path only).
- constraints:
  - no ACL/record-rule/manifest changes;
  - no behavior change for existing signup and activation links.
- acceptance:
  - `py_compile` of changed controllers
  - `make verify.frontend_api` (only if `/api/*` touched; otherwise auth smoke command in dedicated task)

### Batch D (verify)
- objective: verify auth lifecycle regression (signup page + activation callback).
- deliverable: compatibility verification note and rollback checkpoint.

## Risk Model

- `P1`: public auth exposure, user onboarding continuity risk.
- downgrade to `P2` only when target owner is explicit and compatibility tests pass.

## Stop Rules

- stop if any change request touches forbidden high-risk files.
- stop if migration requires implicit ACL changes.
- stop if activation URL compatibility cannot be guaranteed.

## Exit Criteria

All must be true:

1. ownership is single-source and documented.
2. `/web/signup` and `/sc/auth/activate/*` compatibility preserved.
3. auth flow verification passes with explicit rollback recipe.
