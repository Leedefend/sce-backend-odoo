# Capability Registry Steady-State Screen v1

## Goal

Identify the next bounded step required to move capability registry from
"correct but first-request fallback driven" into a true steady-state service
where ordinary `system.init` mainly consumes a prepared artifact.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel verification design
- Module: capability registry steady-state screen
- Module Ownership: task governance only
- Kernel or Scenario: kernel
- Reason: correctness and invalidation boundaries are now verified; the
  remaining issue is lifecycle ownership of the first materialization event

## Current Verified State

Already proven:

- `system.init` now consumes the registry through a bounded artifact service
- invalidation mismatch can be forced and observed correctly on the running
  worker
- repeated requests hit the in-process materialized artifact after the first
  rebuild

Still not steady-state enough:

- the first ordinary request after restart still returns
  `artifact_fallback_used = 1`
- ordinary runtime therefore still pays one live rebuild on the startup chain

So the problem is no longer correctness. It is lifecycle placement.

## Steady-State Requirement

The target steady-state is:

- ordinary `system.init` reads a prepared artifact
- first-request fallback is exceptional, not normal
- rebuild remains explicit and diagnosable when invalidation or corruption
  occurs

## Candidates Screened

### 1. Keep current lazy-first-request behavior

Decision: reject as the next target state

Reason:

- leaves first user request carrying build cost
- keeps `login -> system.init` exposed to a known non-steady behavior
- makes runtime quality depend on request timing rather than controlled
  lifecycle

### 2. Jump directly to persistent cross-process storage

Decision: reject as the immediate next batch

Reason:

- introduces new ownership and lifecycle complexity
- expands persistence semantics before startup ownership is settled
- not required to remove first-request fallback from the ordinary path

### 3. Governance-only manual rebuild entry

Decision: reject as the immediate next batch

Reason:

- useful later, but does not solve cold ordinary startup by itself
- still leaves runtime correctness depending on an external operator action

### 4. Startup/bootstrap warmup of the in-process artifact

Decision: accept as the preferred next bounded step

Reason:

- directly targets the remaining gap: first-request fallback on restart
- stays within the current storage model
- does not require new persistence ownership
- keeps the existing registry service contract intact
- matches the already documented trigger order in materialization design:
  startup/bootstrap warmup first, governance rebuild second, lazy rebuild only
  as fallback

## Chosen Next Step

The next implementation batch should be:

- introduce a controlled startup/bootstrap warmup path that seeds the capability
  registry artifact before ordinary `system.init` traffic

The design intent is not:

- a generic background framework
- a new persistence layer
- a frontend preload trick

It is specifically:

- seed the current in-process materialized artifact at service startup or
  equivalent bootstrap lifecycle point
- keep lazy rebuild only as recovery behavior

## Why This Is The Smallest Valuable Move

This step improves the most important remaining user-visible behavior:

- after restart, the first real user should no longer be the one who pays for
  registry build

And it does so without reopening:

- contract shape
- invalidation semantics
- cross-process persistence
- frontend behavior

## Guardrails For The Next Batch

The startup warmup batch should:

- remain inside backend/kernel ownership
- reuse the current registry artifact service
- avoid introducing business-model assumptions
- emit explicit provenance when warmup succeeded or when runtime had to fall
  back anyway
- keep fallback build path intact as recovery, not delete it

## Recommended Next Batch

Open a bounded implementation batch that:

1. identifies the narrowest startup/bootstrap hook already available in current
   runtime
2. seeds the capability registry artifact through the existing service
3. verifies after restart that the first real `wutao/demo -> system.init`
   request shows `artifact_fallback_used = 0`

That is the next most valuable step because it converts the registry from
"correct runtime cache with recovery" into "prepared startup infrastructure
with recovery".
