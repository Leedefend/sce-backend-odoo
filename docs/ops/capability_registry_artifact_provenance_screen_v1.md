# Capability Registry Artifact Provenance Screen v1

## Goal

Freeze the minimum provenance and fallback semantics for capability registry
artifact consumption before replacing internal rebuild-on-demand behavior with
true materialized reads.

## Current Transitional State

After the first artifact-service implementation batch, the runtime service now
returns:

- `rows`
- `artifact_version`
- `source`
- `fallback_used`
- `fallback_reason`
- `stale`
- `mode`
- `build_meta`

This is enough to introduce ownership semantics, but some fields are still
transitional placeholders rather than frozen contract meanings.

## Frozen Provenance Contract

### 1. `source`

`source` must describe which registry source path produced the artifact
consumed by the caller.

Allowed values for the next implementation phase:

- `materialized_kernel_registry`
- `runtime_query_registry_build`
- `native_projection_fallback`
- `legacy_extension_fallback`
- `capability_model_fallback`

Rule:

- `source` is mandatory whenever an artifact is returned.
- `system.init` and its provider boundary must treat missing/unknown `source` as
  non-authoritative diagnostic debt.

### 2. `fallback_used`

`fallback_used` must mean:

- the artifact did not come from the preferred steady-state source for the
  requested mode

For `mode=runtime`, the preferred steady-state source is:

- `materialized_kernel_registry`

Therefore:

- `fallback_used = false` only when the artifact comes from the preferred
  materialized registry path
- `fallback_used = true` for `runtime_query_registry_build`,
  `native_projection_fallback`, `legacy_extension_fallback`, and
  `capability_model_fallback`

### 3. `fallback_reason`

`fallback_reason` must be non-empty whenever `fallback_used = true`.

Initial allowed reason categories:

- `artifact_missing`
- `artifact_stale`
- `artifact_incompatible`
- `artifact_unavailable`
- `legacy_fallback_enabled`
- `registry_build_exception`

Rule:

- `fallback_reason` is empty only when `fallback_used = false`

### 4. `stale`

`stale` must not mean "current rows feel old" in an informal sense.

It has one narrow meaning:

- the preferred materialized artifact exists or is expected, but is not trusted
  under current invalidation/version rules

Therefore:

- `stale = false` when consuming a valid preferred artifact
- `stale = true` when the preferred artifact is rejected because of version,
  invalidation, or trust mismatch
- `stale` is not the same as `fallback_used`, though stale often leads to
  fallback

## Frozen Ownership Rules

### system.init

May:

- observe artifact provenance indirectly through provider timings/diagnostics

Must not:

- choose fallback policy
- interpret raw registry source modes
- branch on native discovery details

### capability_provider

May:

- consume artifact rows
- surface coarse diagnostic/timing signals
- honor artifact fallback result from the registry service

Must not:

- invent artifact provenance
- become the long-term owner of invalidation rules

### artifact/registry service

Owns:

- `source`
- `fallback_used`
- `fallback_reason`
- `stale`
- build metadata and trust decision

This service is the only legitimate owner of artifact provenance semantics.

## Recommended Next Implementation Direction

The next code batch should:

1. move `fallback_used` from placeholder `false` semantics to explicit policy
2. map current temporary rebuild path to `source=runtime_query_registry_build`
   plus `fallback_used=true`
3. reserve `fallback_used=false` for a future `materialized_kernel_registry`
   success path only
4. prepare a narrow invalidation/trust check seam inside the registry service

That will make the later true-materialization cut-over auditable and
behaviorally explicit.
