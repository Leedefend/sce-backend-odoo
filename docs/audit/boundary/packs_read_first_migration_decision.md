# Packs Read-First Migration Decision (Screen)

- Target family: `/api/packs/*`

## Decision

- read-first implement slice:
  - `/api/packs/catalog`
- write endpoints deferred:
  - `/api/packs/publish`
  - `/api/packs/install`
  - `/api/packs/upgrade`

## Ownership Strategy

- route shell target: **smart_core**
- transition mode: **delegate to scenario pack controller method**
- provider boundary: pack payload/install semantics remain scenario supplied.

## Hard Constraints

1. Read slice must not alter returned catalog schema.
2. Write semantics and quota/limit checks are out of this slice.
3. No ACL/security/manifest/financial changes.

## Stop Signals

- write endpoint included in read slice.
- any modification to install/upgrade side effects.

## Next Implement Slice

- migrate `/api/packs/catalog` route-shell ownership only.
