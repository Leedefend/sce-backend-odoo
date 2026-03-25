# Release Snapshot Lineage Model v1

## Goal

Promote `sc.edition.release.snapshot` from freeze evidence to first-class release promotion target.

## Lifecycle

- `candidate`: created by freeze service, not active, not publishable
- `approved`: passed freeze surface checks, eligible for explicit release
- `released`: active release snapshot for one edition/product surface
- `superseded`: previously released snapshot replaced by a newer released snapshot or rollback target change

## Transition Rules

- `candidate -> approved`
- `approved -> released`
- `candidate -> released`
  - allowed only through the promotion service to preserve explicit replace protocol
- `released -> superseded`
- all other transitions are invalid

## Active Uniqueness

For one `product_key`, only one snapshot may satisfy:

- `state == released`
- `is_active == true`

Promotion to a new released snapshot must use explicit replacement. The previous active released snapshot is marked `superseded` and linked via `replaced_by_snapshot_id`.

## Runtime Diagnostics

`system.init.data.edition_runtime_v1.diagnostics.released_snapshot_lineage` now exposes:

- `snapshot_id`
- `product_key`
- `edition_key`
- `version`
- `state`
- `is_active`
- `released_at`
- `approved_at`
- `frozen_at`
- `state_reason`
- `promotion_note`
- `promoted_from_snapshot_id`
- `rollback_target_snapshot_id`
- `replaced_by_snapshot_id`
- `effective_runtime`

## Rollback Basis

Rollback is anchored on release snapshot lineage, not transient runtime state. A released snapshot may point to `rollback_target_snapshot_id`, and rollback reactivates a prior released/approved snapshot under explicit service control.
