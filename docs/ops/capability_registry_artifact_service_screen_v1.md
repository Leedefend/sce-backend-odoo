# Capability Registry Artifact Service Screen v1

## Goal

Map the materialization design to the current codebase and define the smallest
implementation-ready artifact service interface plus the exact `system.init`
cut-over points.

## Current Cut-Over Points

### 1. `system.init` consumer

Current consumer path:

- `addons/smart_core/handlers/system_init.py`
- `_load_capabilities_for_user_with_timings(env, user)`
- `prepare_runtime_context.load_capabilities_for_user`

`system.init` itself already has a narrow consumer seam. It does not directly
call native adapters; it calls the capability provider boundary.

### 2. Capability provider boundary

Current provider path:

- `addons/smart_core/core/capability_provider.py`
- `load_capabilities_for_user_with_timings(...)`

This is the main cut-over seam. Today it does:

1. call `CapabilityRegistryService.get_registry_bundle_with_timings(...)`
2. build runtime projection from returned `rows`
3. if needed, fall back to legacy extension/model-based paths

So the first implementation batch should cut over here, not inside
`system_init.py`.

### 3. Current registry service

Current service:

- `addons/smart_core/app_config_engine/capability/services/capability_registry_service.py`

Today this service is only a thin wrapper around:

- `CapabilityRegistry.build_with_timings(...)`

which still rebuilds rows on demand.

## Proposed Minimum Artifact Service Interface

The first artifact service interface should remain narrow:

```text
get_registry_artifact_with_timings(env, user=None, mode="runtime")
  -> artifact, timings
```

Where `artifact` minimally contains:

- `rows`
- `artifact_version`
- `source`
- `fallback_used`
- `fallback_reason`
- `stale`
- `build_meta`

The first batch does not need to implement every future mode; it only needs:

- `runtime` mainline consumption
- explicit fallback provenance

## Proposed Ownership Split

### Artifact service owns

- locate/read materialized artifact
- decide whether artifact is missing/stale
- trigger or delegate rebuild under controlled policy
- return explicit provenance/fallback metadata

### Capability provider owns

- consume artifact rows
- build runtime capability list projection
- preserve current outward return shape to `system.init`

### system.init owns

- consume provider result only
- record timings/diagnostics only

## First Implementation Write Scope

The first cut-over batch can stay bounded to these files:

- `addons/smart_core/app_config_engine/capability/services/capability_registry_service.py`
- `addons/smart_core/core/capability_provider.py`

Optional third file only if needed for artifact structure helpers:

- a new service/helper file under
  `addons/smart_core/app_config_engine/capability/services/`

`system_init.py` should not need semantic restructuring for the first cut-over.

## Fallback Owner

The first fallback owner should remain below the capability provider boundary,
not inside `system.init`.

That means:

- artifact service may report `fallback_used = true`
- capability provider may still choose legacy projection path temporarily
- but `system.init` should only observe metadata/timings, not control fallback

## Recommended First Implementation Batch

The first implementation batch should do only this:

1. introduce artifact-returning registry service API
2. preserve current rebuild path behind that service as temporary implementation
3. expose provenance fields so later batches can replace rebuild-on-demand with
   true materialized reads
4. cut `capability_provider.py` over to artifact consumption semantics

This keeps the first code batch small while aligning the ownership model before
any deeper materialization backend is introduced.
