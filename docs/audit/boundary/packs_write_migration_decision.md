# Packs Write Migration Decision (Screen)

- Target endpoints:
  - `/api/packs/publish`
  - `/api/packs/install`
  - `/api/packs/upgrade`

## Decision

- migration mode: **single bounded implement batch** with route-shell ownership transfer only.
- target ownership: **smart_core route shell**.
- semantic handling: **delegate writes to existing scenario pack controller methods**.

## Hard Constraints

1. No write semantic change (publish/install/upgrade side effects unchanged).
2. No auth change (`_has_admin` checks preserved through delegation).
3. No ACL/security/manifest/financial domain changes.

## Stop Signals

- any attempt to rewrite pack install/upgrade internals.
- any change touching authority models/rules.
- inability to pass smoke verification after migration.

## Next Implement Slice

- migrate these 3 write routes to smart_core delegation controller and verify.
