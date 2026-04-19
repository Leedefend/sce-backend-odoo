# Capability Registry Durable Source Screen v1

## Goal

Choose the next bounded upgrade behind the registry service so the current
placeholder in-process artifact cache becomes more durable and
invalidation-aware without breaking the service contract already consumed by
`capability_provider.py` and `system.init`.

## Current State

The current implementation already proves two behaviors:

- first runtime request: explicit fallback rebuild
- second runtime request on the same process: materialized read success

The current materialized source is an in-process cache keyed by:

- db
- platform owner
- mode
- user

This proves the contract shape, but durability is still limited to one process
lifespan and invalidation is not yet explicit.

## Reusable Existing Assets

### 1. Versioning rules already exist

`docs/contract/versioning_rules.md` already freezes:

- `api_version`
- `contract_version`
- `schema_version`
- same-version snapshot stability

So the durable source upgrade should reuse versioned artifact thinking, not
invent a parallel, unversioned cache model.

### 2. Snapshot/export semantics already exist in the repo

Example:

- `docs/contract/exports/scene_catalog.json`

This file already demonstrates a pattern the repo accepts:

- exported artifact
- explicit source metadata
- schema/version markers
- stable shape for downstream consumption

That means the next durable source does not need to invent a new philosophy.
It can follow the same “versioned artifact with explicit provenance” model.

## Chosen Next Bounded Upgrade

The next bounded upgrade should be:

- a versioned in-memory artifact store with explicit invalidation keys

Not yet:

- database persistence
- new model
- filesystem-backed runtime store
- cross-process cache dependency

Reason:

- it stays inside the current low-risk write surface
- it upgrades trust semantics before storage medium complexity
- it preserves the current registry service contract

## Durable Source Design

### 1. Stored artifact contents

The cached artifact should additionally carry:

- `artifact_version`
- `build_meta.invalidation_key`
- `build_meta.contract_version`
- `build_meta.schema_version`
- `build_meta.platform_owner`
- `build_meta.mode`

### 2. Invalidation key inputs

The next invalidation key should be derived from stable inputs already available
to the kernel:

- registry artifact version
- platform owner
- mode
- extension module set / contribution source signature
- contract/schema version markers used by the consumer contract

This is enough for the next phase to detect:

- same-process usable artifact
- same-process stale artifact after relevant semantic drift

### 3. Success policy

Materialized read success remains allowed only when:

- provenance is complete
- artifact version is supported
- invalidation key matches current expected key
- source remains `materialized_kernel_registry`
- fallback flags remain false

### 4. Rebuild policy

If invalidation key mismatches:

- mark artifact stale
- return explicit fallback artifact
- rebuild and reseed in-process store

This is a meaningful durability upgrade even before any persistent store exists.

## Why Not Persistent Storage Yet

Persistent storage is a later step because it adds new risks:

- persistence ownership
- write timing / lifecycle hooks
- cross-process freshness
- cleanup and backward compatibility

The next bounded batch should improve trust and invalidation first, while
keeping storage medium complexity flat.

## Recommended Next Implementation Batch

Implement:

1. explicit invalidation key derivation in the registry service
2. artifact cache entries carrying version/invalidation metadata
3. trust check upgraded from placeholder guard to invalidation-aware guard
4. reseed-on-mismatch behavior behind the same service contract

This keeps the runtime contract stable while making the artifact source more
durable in the way that matters first: trust semantics.
