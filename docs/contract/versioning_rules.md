# Contract Versioning Rules (R5)

## Scope

This rule set governs Smart Core contract compatibility for:

- `system.init`
- `ui.contract`
- write-intent envelopes used by frontend runtime

## Version Fields

Contract responses should expose version metadata in `meta`:

- `api_version`
- `contract_version`
- `schema_version` (when available)

## Compatibility Policy

### Additive-first

- New fields must be additive.
- Existing required fields must not be removed in the same major line.

### Required envelope stability

Runtime responses must keep envelope keys:

- top-level: `ok`, `data`, `meta`
- error path: `ok=false`, `error`, and stable `reason_code` semantics

### Rename/deprecate policy

- Renames require a compatibility window.
- During the window, both old and new fields should be present or bridged.
- Removal requires major upgrade and changelog entry.

### Frontend tolerance contract

Frontend must tolerate:

- extra fields (unknown keys)
- missing optional fields

Frontend must not assume:

- deterministic ordering of object keys
- presence of undocumented internal fields

## Snapshot and Drift Rules

- Same-version snapshots must be stable under deterministic inputs.
- Cross-version diff must be explainable by changelog and version bump.

## R5 Validation Mapping

- `make verify.contract.compat` validates runtime envelope/version fields and required keys.
- `make verify.contract.snapshot` keeps same-version output stable.

