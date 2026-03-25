# Release Audit Trail Model v1

## Goal

Define a single audit surface for release governance without changing released runtime semantics.

## Layer Target

- Platform Layer
- Delivery Runtime Layer
- Release Governance Layer

## Module

- `addons/smart_core/delivery/release_audit_trail_service.py`
- `addons/smart_core/models/release_action.py`
- `addons/smart_core/models/edition_release_snapshot.py`
- `addons/smart_core/handlers/system_init.py`

## Reason

Promotion and rollback are already executable. This batch makes them auditable, explainable, and exportable from one governed surface.

## Contract

`release_audit_trail_surface_v1` contains:

1. `identity`
2. `active_released_snapshot`
3. `release_actions`
4. `release_snapshots`
5. `lineage`
6. `rollback_evidence`
7. `runtime`

## Rules

- No new release governance model is introduced.
- Audit surface is derived from `sc.release.action` and `sc.edition.release.snapshot`.
- `system.init` keeps existing fields and only adds additive diagnostics.
- Runtime must expose the current released snapshot hit through `release_audit_trail_summary`.

## Verification

- `verify.release.audit_surface_guard`
- `verify.release.audit_lineage_consistency_guard`
- `verify.release.audit_runtime_consistency_guard`
- `verify.release.audit_trail.v1`
