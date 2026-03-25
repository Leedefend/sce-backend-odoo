# Release Snapshot Lineage Surface v1

## Scope

This surface governs edition release snapshots for:

- `construction.standard`
- `construction.preview`

It does not reopen FR-1 to FR-5, released navigation, Scene Asset v1, Delivery Engine v1, Edition Runtime Routing v1, or Edition Freeze Surface v1 semantics.

## Release Surface Contract

Runtime release snapshot lineage is surfaced through:

- `system.init.data.edition_runtime_v1.diagnostics.released_snapshot_lineage`
- `delivery_engine_v1.meta.released_snapshot_lineage`

## Promotion Protocol

Freeze now creates a `candidate` snapshot and promotes it through explicit lineage:

1. `candidate`
2. `approved`
3. `released`
4. `superseded`

Replacing the active released snapshot for one edition is explicit and auditable.

## Guards

- `make verify.release_snapshot.promotion_guard`
- `make verify.release_snapshot.active_uniqueness_guard`
- `make verify.release_snapshot.lineage_guard`
- `make verify.release.snapshot_lineage.v1`

## Expected Outcome

- one active released snapshot per edition/product surface
- runtime diagnostics always point to the resolved released snapshot lineage
- rollback evidence remains anchored on release snapshots rather than transient runtime results
