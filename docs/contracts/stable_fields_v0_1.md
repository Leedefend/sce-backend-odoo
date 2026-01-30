# Stable Response Fields v0.1

This document defines the minimal stable response fields for core contract flows.

## Scope
- `system.init`
- `ui.contract`

## Envelope (intent responses)

Common envelope keys:
- `ok`: boolean
- `data`: object (payload)
- `meta`: object (metadata)

Stable metadata fields (added in v0.1):
- `meta.contract_version`: string, e.g. `v0.1`
- `meta.api_version`: string, e.g. `v1`

These fields allow clients to detect contract schema changes and apply compatibility logic.

## Compatibility rules
- **New fields** are backward-compatible and may be added in any minor version.
- **Removing or renaming fields** requires a **major** version bump.
- **Behavior changes** (same fields, different meaning) must be documented in a migration note.

## ETag policy
- ETag MUST change when `contract_version` changes.
- Clients MUST treat different `contract_version` values as incompatible cached schema.

## Notes
- `contract_version` is a contract schema marker for client compatibility.
- `api_version` tracks the intent API surface (routing, auth, error envelope).
