# Capability Registry Invalidation Synthetic Verify Screen v1

## Goal

Define the smallest safe verification seam for forcing an invalidation-key
mismatch without mutating installed module state or adding an unsafe general
runtime switch.

## Verified Current State

Already proven on live runtime:

- first request after restart -> explicit fallback
- second request on same process -> materialized hit

Not yet safely proven on live runtime:

- stale cached artifact rejected because invalidation key mismatches

## Why Direct Live Injection Is Unsafe

The current invalidation key depends on:

- artifact version
- contract/schema version
- platform owner
- mode
- installed `smart_*` module set

Changing those inputs directly in live verification would require one of:

- mutating installed module state
- mutating code constants
- adding a broad runtime override

All three are too risky for ordinary verification.

## Chosen Safe Seam

The smallest safe seam is:

- a verification-only synthetic invalidation salt input owned by the registry
  service

Characteristics:

- only read in explicit verification mode
- additive
- ignored in ordinary runtime
- folded into `expected_invalidation_key`
- absent by default

Recommended form:

- a narrowly named environment variable or debug-only config parameter such as
  `SMART_CORE_CAPABILITY_REGISTRY_VERIFY_SALT`

Rules:

- only used by the registry service
- only affects invalidation-key derivation
- does not alter capability rows or business semantics
- not surfaced to frontend contracts

## Recommended Next Batch

Implement a tiny verification seam that:

1. optionally appends a verification-only salt to the invalidation-key payload
2. is off by default
3. can be toggled in live verification to force stale mismatch
4. keeps ordinary runtime semantics unchanged

Then the follow-up verify batch can prove:

- normal materialized hit under unchanged key
- forced stale mismatch under synthetic salt change
- fallback + reseed after mismatch
