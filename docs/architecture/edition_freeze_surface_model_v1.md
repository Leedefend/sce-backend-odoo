# Edition Freeze Surface Model v1

## Goal

Upgrade edition delivery from a runtime-accessible channel to a freezeable, replayable, auditable release surface.

## Scope

This batch governs:

- `construction.standard`
- `construction.preview`

It does not reopen FR-1 to FR-5, does not rewrite released navigation, and does not replace Delivery Engine v1 runtime resolution.

## Layer Target

- Platform Layer: `addons/smart_core/models/edition_release_snapshot.py`
- Delivery Runtime Layer: `addons/smart_core/delivery/edition_release_snapshot_service.py`
- Release Governance Layer: `scripts/verify/edition_*_guard.sh`

## Asset Model

Model: `sc.edition.release.snapshot`

Required fields:

- `product_key`
- `base_product_key`
- `edition_key`
- `version`
- `channel`
- `snapshot_json`
- `is_active`

Governance fields:

- `frozen_at`
- `activated_at`
- `superseded_at`
- `source_policy_id`
- `rollback_target_snapshot_id`
- `replaced_by_snapshot_id`
- `meta_json`

Uniqueness:

- `(product_key, version)` must be unique

## Freeze Surface Payload

`snapshot_json` is standardized as `edition_freeze_surface_v1`:

- `identity`
- `policy`
- `nav`
- `capabilities`
- `scenes`
- `scene_version_bindings`
- `scene_binding_diagnostics`
- `runtime_meta`

## Freeze Flow

```text
product policy + delivery_engine_v1
-> edition freeze surface payload
-> sc.edition.release.snapshot
```

Freeze is explicit. Runtime delivery still resolves from product policy and scene assets; release snapshots are freeze evidence and rollback basis.

## Active Snapshot Rule

For one `product_key`, only one edition release snapshot should be active.

Freeze with `replace_active=True`:

- activates the new snapshot
- supersedes the previous active snapshot
- records `rollback_target_snapshot_id`

## Rollback Basis

Rollback uses explicit frozen release evidence:

```text
active release snapshot
-> rollback_target_snapshot_id
-> previous active release snapshot
```

This enables deterministic rollback without mutating released navigation or scene runtime semantics.

## Guard Baseline

- `make verify.edition.freeze_surface_guard`
- `make verify.edition.release_snapshot_guard`
- `make verify.edition.rollback_evidence_guard`
- `make verify.release.edition_freeze.v1`
