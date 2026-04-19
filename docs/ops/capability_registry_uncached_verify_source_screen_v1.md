# Capability Registry Uncached Verify Source Screen v1

## Goal

Choose the smallest uncached verification-only salt source that the already
running worker can observe immediately, without reopening product semantics or
adding a broad new debug subsystem.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: capability registry uncached verification source screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: the previous boundary screen proved that `ir.config_parameter.get_param()`
  is process-cached and therefore unsuitable as the live-toggle read path for
  this verification objective

## Hard Constraints

The next source must remain:

- backend-only
- verification-only
- absent by default
- additive
- scoped to `CapabilityRegistryService`
- limited to invalidation-key derivation
- removable after verification without public-contract impact

## Candidates Screened

### 1. Keep using `ir.config_parameter.get_param()`

Decision: reject

Reason:

- blocked by `@ormcache('key')`
- already proven not to satisfy same-worker freshness

### 2. Add another config parameter key and still read it via `get_param()`

Decision: reject

Reason:

- same cache boundary, new key or old key does not matter
- adds naming surface without solving the runtime problem

### 3. Add a new model/table for verification-only diagnostics

Decision: reject for now

Reason:

- expands write scope and ownership too early
- creates unnecessary persistence/design surface for a bounded verification need

### 4. Read the same verification key through direct SQL inside the registry service

Decision: accept as preferred next source

Recommended key:

- `smart_core.capability_registry.verify_salt`

Recommended read semantics:

- verification-only helper in `CapabilityRegistryService`
- direct SQL against `ir_config_parameter`
- fallback to existing environment variable seam if SQL returns empty

Reason:

- smallest delta from the current design
- keeps the already chosen key name and ownership
- bypasses `get_param()` cache semantics
- does not require new schema or new business facts
- remains tightly bounded to service-local verification logic

## Chosen Design

The next implementation batch should:

1. keep the existing key name `smart_core.capability_registry.verify_salt`
2. stop reading that key through `get_param()` for live verification
3. add a service-local uncached SQL read helper
4. use that helper only for verification-salt derivation
5. keep environment variable fallback for startup-controlled synthetic verify

## Why This Is The Smallest Safe Move

This choice avoids:

- introducing a new persistent artifact type
- changing contract shape
- adding frontend-visible diagnostics
- modifying ordinary business facts
- depending on cross-process ORM cache behavior

At the same time, it preserves:

- the existing verification key name
- the existing fallback order philosophy
- the existing capability artifact contract

## Guardrails For The Next Batch

The uncached SQL helper must:

- live only inside `CapabilityRegistryService`
- read only the verification key
- return empty string on absence/failure
- never affect capability rows directly
- never run outside invalidation-key derivation
- never be promoted into ordinary config-reading guidance

## Recommended Next Batch

Open a bounded implementation task that replaces the current
`ir.config_parameter.get_param()` live-toggle read with a service-local
uncached SQL read for `smart_core.capability_registry.verify_salt`, then rerun
the same live stale-mismatch verification chain on the running worker.
