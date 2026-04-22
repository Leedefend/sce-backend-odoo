# Ops Write Migration Decision (Screen)

- Target endpoints:
  - `/api/ops/subscription/set`
  - `/api/ops/packs/batch_upgrade`
  - `/api/ops/packs/batch_rollback`

## Decision

- migration mode: **single bounded implement batch** with route-shell ownership transfer only.
- target ownership: **smart_core route shell**.
- semantic handling: **delegate writes to existing scenario ops controller methods**.

## Hard Constraints

1. No write semantic change (payload/side effects/status flow unchanged).
2. No auth escalation change (`_has_admin` checks preserved through delegation).
3. No ACL/security/manifest/financial domain changes.

## Stop Signals

- any attempt to rewrite job execution or pack rollout logic.
- any change touching authority models/rules.
- inability to prove smoke compatibility after migration.

## Next Implement Slice

- Migrate these 3 write routes to smart_core delegation controller and verify with standard frontend API smoke.
