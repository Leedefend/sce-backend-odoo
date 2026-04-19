# Capability Registry Materialization Design v1

## Goal

Provide an implementation-grade design for how capability registry should be
built, cached/materialized, invalidated, and consumed by `system.init` so the
main startup path stops depending on repeated request-time native discovery.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel design
- Module: capability registry materialization design
- Module Ownership: docs + task governance only
- Kernel or Scenario: kernel
- Reason: boundary recovery has already established that current
  `native_projection` in `system.init` is a transition-state discovery path;
  the next step is to define the replacement contract

## Design Decision

### 1. Build trigger

Capability registry materialization should be triggered by controlled kernel
events, not by every ordinary `system.init` request.

Preferred trigger order:

1. startup/bootstrap warmup when registry artifact is absent
2. explicit governance rebuild path
3. version/invalidation-triggered lazy rebuild on first consumer only when
   artifact is stale or missing

Ordinary steady-state `system.init` must not be the normal build trigger.

### 2. Materialization artifact

`system.init` mainline should consume a materialized artifact that contains:

- canonical capability rows
- stable capability keys and semantic fields
- artifact version metadata
- provenance/fallback flags
- build timestamp / build source

The artifact should be treated as a kernel runtime/shared-service output, not
as an ad hoc per-request reconstruction.

### 3. Materialization location

The acceptable materialization location is:

- platform-kernel shared-service cache / registry layer

This location may be backed by:

- in-process cache for fast read
- optional persisted snapshot/export for governance or warm restart support

But the main design rule is:

- `system.init` reads from the shared materialized registry interface
- `system.init` does not directly orchestrate broad native discovery

### 4. Fallback trigger

`native_projection` remains allowed only when one of these explicit conditions
holds:

- no materialized registry artifact exists
- artifact version is incompatible with current kernel expectations
- governance/debug mode explicitly asks for rebuild/audit
- recovery mode is entered after artifact corruption or missing dependency facts

Fallback must be explicit and diagnosable. It should set provenance such as:

- `source = native_projection_fallback`
- `fallback_reason = <...>`

Steady-state success path should instead expose:

- `source = materialized_kernel_registry`

### 5. Invalidation semantics

Registry invalidation should be versioned and explainable.

Minimum invalidation inputs:

- kernel contract/schema version affecting capability shape
- installed/active extension module set affecting capability contributions
- registry build policy version
- optional capability-definition source revision

If any of those inputs change, the artifact is stale and must rebuild before it
is trusted as the mainline source.

### 6. Mainline system.init contract

`system.init` should be allowed to consume only:

- materialized capability registry artifact
- explicit fallback artifact returned by the registry service when fallback was
  required

`system.init` should not own:

- raw native adapter fan-out
- direct menu/action/model/report/view-binding scans
- artifact build policy decisions

Those belong below it in the kernel shared-service/materialization layer.

## Suggested Service Contract

The eventual kernel-facing interface should conceptually look like:

```text
get_capability_registry_artifact(env, user, mode=runtime)
  -> artifact
     - rows
     - artifact_version
     - source
     - fallback_used
     - fallback_reason
     - stale
     - build_meta
```

Where:

- `runtime` mode is what `system.init` uses
- separate governance mode may permit rebuild/audit visibility

## Design Consequence

The next implementation batch should not optimize another native adapter first.

It should introduce or refactor toward:

1. a materialized registry service boundary
2. explicit artifact metadata and provenance
3. invalidation/version checks
4. a `system.init` consumer path that reads the artifact instead of rebuilding
   it implicitly

## Verification Consequence

When this design is implemented, verification should prove:

- repeated `system.init` calls read the same artifact without native rebuild
- fallback path is explicit and auditable
- version/invalidation change forces rebuild exactly when expected
- current snapshot stability guarantees still hold
