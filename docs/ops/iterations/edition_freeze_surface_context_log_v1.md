# Edition Freeze Surface Context Log v1

## Goal

Freeze current released edition delivery surfaces into explicit release snapshot assets.

## Governed Assets

- `sc.edition.release.snapshot`
- `EditionReleaseSnapshotService`
- `edition_freeze_surface_v1`

## First Batch

- `construction.standard`
- `construction.preview`

## Frozen Payload Sections

- `identity`
- `policy`
- `nav`
- `capabilities`
- `scenes`
- `scene_version_bindings`
- `scene_binding_diagnostics`
- `runtime_meta`

## Rollback Rule

Rollback is evidence-based:

- freeze a new active release snapshot
- preserve the previous active release snapshot as `rollback_target_snapshot_id`
- rollback explicitly reactivates that target snapshot

## Out of Scope

- no runtime swap to release snapshot truth
- no new edition admin UI
- no released navigation rewrite
- no reopened FR-1 to FR-5 semantics
