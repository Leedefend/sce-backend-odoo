# Ops Read-First Migration Decision (Screen)

- Target family: `/api/ops/*`
- Decision Stage: `screen`
- Inputs:
  - `docs/audit/boundary/runtime_priority_matrix.md`
  - `docs/audit/boundary/governance_endpoint_ownership_decision.md`

## Decision

- read-first implement slice:
  - `/api/ops/tenants`
  - `/api/ops/audit/search`
  - `/api/ops/job/status`
- write endpoints deferred to next slices:
  - `/api/ops/subscription/set`
  - `/api/ops/packs/batch_upgrade`
  - `/api/ops/packs/batch_rollback`

## Ownership Strategy

- route shell target: **smart_core**
- transition execution: **delegate to scenario ops controller methods**
- provider boundary: governance facts/jobs remain scenario-supplied.

## Hard Constraints

1. Read-slice migration must not alter auth semantics or response schema.
2. Write/batch operations remain frozen in current owner for this slice.
3. No ACL/security/manifest side changes.

## Stop Signals

- Any write endpoint included in read-first batch.
- Any change to job execution semantics in this slice.
- Any authority leakage uncertainty in admin checks.

## Next Implement Slice

- Implement smart_core route-shell ownership for the three read endpoints only.
