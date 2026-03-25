# Release Snapshot Lineage Context Log v1

## Batch Goal

Upgrade edition release snapshots from freeze evidence to release promotion lineage assets.

## What Changed

- `sc.edition.release.snapshot` now has lifecycle states: `candidate / approved / released / superseded`
- `EditionReleaseSnapshotPromotionService` now controls promotion and explicit replacement
- runtime diagnostics expose the resolved released snapshot lineage
- release gate now includes promotion, lineage, and active uniqueness guards

## Non-Goals Preserved

- FR-1 to FR-5 remain frozen
- released navigation remains unchanged
- standard surface semantics remain unchanged
- scene asset and delivery engine semantics remain additive only

## Recovery Anchor

If a later batch changes edition runtime behavior, first verify:

1. `make verify.release.edition_freeze.v1 ...`
2. `make verify.release.snapshot_lineage.v1 ...`

before changing policy resolution or runtime diagnostics.
