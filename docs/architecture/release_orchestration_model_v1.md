# Release Orchestration Model v1

## Goal

Upgrade release promotion and rollback from standalone capabilities into auditable release actions.

## Core Asset

`sc.release.action` is the orchestration record for one release operation.

### Fields

- `action_type`
  - `promote_snapshot`
  - `rollback_snapshot`
- `state`
  - `pending`
  - `running`
  - `succeeded`
  - `failed`
- `product_key`
- `base_product_key`
- `edition_key`
- `source_snapshot_id`
- `target_snapshot_id`
- `result_snapshot_id`
- `request_payload_json`
- `result_payload_json`
- `diagnostics_json`
- `reason_code`
- `requested_at`
- `executed_at`
- `completed_at`

## Orchestration Rule

`ReleaseOrchestrator` is the only orchestration entry in this batch.

It wraps:

- `EditionReleaseSnapshotPromotionService`
- `EditionReleaseSnapshotService.rollback_to_snapshot`

under one savepoint so that:

- action record exists before execution
- runtime state changes are atomic inside savepoint
- success/failure is written back to `sc.release.action`

## Atomicity Boundary

Each release action follows:

1. create `pending` action
2. mark `running`
3. execute promote or rollback inside savepoint
4. mark `succeeded` or `failed`

The batch does not introduce admin UI or async job execution.

## Non-Goals

- no new release admin scene
- no workflow approval chain
- no change to released navigation or standard runtime semantics
