# Capability Registry Materialized Read Guard Screen v1

## Goal

Freeze the exact success semantics and guard conditions for switching runtime
mode from explicit fallback rebuilds to true materialized registry reads.

## Success Semantics For `mode=runtime`

A materialized registry read is considered **successful** only when all of the
following are true:

1. `source == "materialized_kernel_registry"`
2. `fallback_used == false`
3. `fallback_reason == ""`
4. `stale == false`
5. `artifact_version` is present and supported by the current consumer
6. `rows` is a list
7. `build_meta` is present as a dict

Only this combination counts as a real mainline materialized read success.

## Guarded Non-Success Combinations

The following combinations must **not** be treated as materialized-read success:

### A. Missing provenance

If any of these is missing:

- `source`
- `artifact_version`
- `build_meta`

then the artifact is not trustworthy enough for runtime success.

Required behavior:

- do not mark success
- fall back or treat as artifact-unavailable

### B. Preferred source mismatch

If:

- `source != "materialized_kernel_registry"`

then runtime success is blocked, even if rows exist.

Required behavior:

- treat as fallback path

### C. Explicit fallback

If:

- `fallback_used == true`

then runtime success is blocked by definition.

Required behavior:

- treat as fallback path

### D. Stale artifact

If:

- `stale == true`

then runtime success is blocked even if source is materialized.

Required behavior:

- artifact must be rejected for steady-state runtime success
- fallback or rebuild path may be used according to service policy

### E. Unsupported artifact version

If:

- `artifact_version` is present but unsupported by current kernel consumer

then runtime success is blocked.

Required behavior:

- `fallback_used = true`
- `fallback_reason = artifact_incompatible`

### F. Empty or invalid row payload

If:

- `rows` is not a list

then runtime success is blocked.

If:

- `rows == []`

this is not automatically a failure, but it must only be accepted as success if
the materialized source itself is trusted and empty rows are semantically valid.

For the next implementation phase, safer default policy is:

- empty rows from materialized source should still be considered suspicious and
  should keep fallback eligible unless explicitly proven valid by a later rule

## Frozen Guard Conditions

For the next implementation batch, the registry service should switch runtime
success only when:

- provenance is complete
- source is `materialized_kernel_registry`
- artifact is not stale
- version is supported

Otherwise it must return an explicit fallback artifact.

## Ownership Rule

These guards belong to the registry artifact service, not to:

- `system.init`
- `capability_provider`

Those consumers may observe the result, but they must not redefine success.

## Recommended Next Implementation Batch

The next code batch should introduce:

1. a trust-check seam inside the registry service
2. explicit success/fallback branching based on these guard conditions
3. a temporary materialized-read placeholder path that can later be wired to a
   real cache/snapshot backend without changing consumer semantics
