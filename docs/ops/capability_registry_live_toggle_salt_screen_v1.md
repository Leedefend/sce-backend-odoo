# Capability Registry Live-Toggle Salt Screen v1

## Goal

Choose the narrowest verification-only salt source that can be toggled on an
already running Odoo process so stale invalidation mismatch can be proven
without mutating installed module state or widening runtime ownership.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: registry invalidation live-toggle salt screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: the current verification-only environment salt is safe, but it is
  only process-start toggleable and therefore cannot complete live stale
  mismatch verification on an already running worker

## Current Verified Constraint

The registry service currently derives the optional verification salt from:

- `SMART_CORE_CAPABILITY_REGISTRY_VERIFY_SALT`

This seam is acceptable for synthetic verification design because it is:

- additive
- absent by default
- service-owned
- not exposed to frontend contracts

But it is not sufficient for live mismatch verification on an already running
Odoo worker, because environment-variable changes are not a reliable runtime
toggle inside the existing process.

## Screening Criteria

The replacement or companion source must satisfy all of the following:

1. live-toggleable on an already running Odoo process
2. verification-only by naming and ownership
3. scoped to the registry service invalidation key only
4. absent by default
5. additive, with no business semantic effect
6. not dependent on installed-module mutation
7. not surfaced to `system.init` consumers except through existing artifact
   provenance fields

## Candidates Screened

### 1. Keep environment variable only

Decision: reject for live verification

Reason:

- safe but not reliably toggleable for the already running worker
- requires restart or process bootstrap control, which defeats the purpose of
  this verification batch

### 2. Reuse installed-module state as synthetic input

Decision: reject

Reason:

- mutates real runtime facts
- crosses from verification seam into module-state mutation
- violates the current low-risk verification boundary

### 3. Use a broad generic debug switch

Decision: reject

Reason:

- ownership becomes unclear
- broad debug inputs are too easy to leak into ordinary runtime
- expands the seam beyond registry invalidation needs

### 4. Use a narrow debug-only `ir.config_parameter`

Decision: accept as the preferred next seam

Recommended key:

- `smart_core.capability_registry.verify_salt`

Reason:

- live-toggleable on a running Odoo process
- already belongs to backend service-owned configuration semantics
- can be read only by the registry service
- can remain absent by default
- does not require module-state mutation
- can be constrained to verification use by explicit name and docs

## Chosen Design

The next bounded seam should be:

- keep the current environment salt for process-start synthetic verification
- add a narrower live-toggleable companion read from a debug-only
  `ir.config_parameter`

Recommended precedence:

1. explicit debug-only `ir.config_parameter`
2. fallback to `SMART_CORE_CAPABILITY_REGISTRY_VERIFY_SALT`
3. default empty salt

Why this precedence is preferred:

- live verification can be completed without restart
- existing synthetic seam remains usable in non-live or startup-controlled
  verification
- ordinary runtime remains unchanged when both sources are absent

## Guardrails

The live-toggle key must obey these limits:

- read only inside `CapabilityRegistryService`
- folded only into invalidation-key derivation
- never used to alter capability rows
- never used to alter business facts
- never returned as a public contract field
- absent from frontend/runtime user-facing behavior
- documented as verification-only and off by default

## Verification Path Enabled By This Choice

Once the live-toggle companion seam exists, the stale-mismatch proof can be run
as:

1. start with empty live-toggle salt
2. issue request and seed materialized artifact
3. issue second request and confirm materialized hit
4. set `smart_core.capability_registry.verify_salt` on the running system
5. issue another request
6. confirm stale mismatch rejection, explicit fallback, and reseed
7. clear the key and confirm steady-state returns to normal

This proves mismatch behavior without mutating installed modules or restarting
the worker.

## Recommended Next Batch

Open a bounded implementation batch that:

1. adds a verification-only `ir.config_parameter` read in the registry service
2. preserves the current environment-variable seam as fallback
3. keeps default runtime behavior unchanged when both salts are absent
4. follows immediately with a live verification batch proving stale mismatch,
   fallback, and reseed on the running worker
