# Capability Registry Boundary Recovery Screen v1

## Goal

Recover a clean ownership boundary for capability registry so that `system.init`
consumes a stable platform fact source instead of depending on an ambiguous
request-time native discovery path.

## Fixed Architecture Declaration

- Layer Target: Platform-kernel boundary diagnostics
- Module: capability registry boundary recovery screen
- Module Ownership: docs + task governance only
- Kernel or Scenario: kernel
- Reason: the prior ownership screen established that current
  `native_projection` on the `system.init` hot path is a transition-state
  discovery mechanism rather than an ideal steady-state source of truth

## Boundary Inputs

### 1. Target architecture

`docs/architecture/enterprise_pm_paas_target_architecture_v1.md` places:

- `Intent Runtime`
- `Contract Runtime`
- `Metadata Center`
- `Scene Orchestrator`
- `Platform Shared Services`

inside the platform kernel.

It explicitly allows:

- `scene catalog / capability registry`
- `runtime bootstrap / system init`

as controlled runtime/reading capabilities, but it does not require those
capabilities to rediscover native objects on every request.

### 2. Current implementation mapping

`docs/architecture/enterprise_pm_paas_implementation_mapping_v1.md` already
states the desired runtime direction as:

```text
intent -> base contract -> scene orchestrator -> scene-ready contract
```

So the recovery direction should reduce request-time discovery and increase
stable kernel fact consumption.

### 3. Ownership screen result

The previous screen established:

- `native_projection` is not simply consuming already-materialized intent facts
- it is better classified as bootstrap / compatibility projection
- keeping it in the `system.init` hot path creates a transition-state overlap

## Recovery Decision

### A. Canonical fact source

The canonical fact source for capability registry should be:

- stable capability semantics owned by the platform kernel
- materialized as a registry-ready kernel fact set
- consumed by `system.init`, not rediscovered inside `system.init`

This means the long-term truth source is **not**:

- raw `ir.ui.menu`
- raw `ir.actions.*`
- raw `ir.model` / `ir.model.access`
- raw view-binding tables

Those native objects may inform bootstrap or registry generation, but they
should not remain the primary steady-state fact source of runtime bootstrap.

### B. Fallback allowance

`native_projection` remains allowed only as a controlled fallback under explicit
conditions such as:

- bootstrap initialization when no materialized capability registry exists
- compatibility recovery for older modules or missing registry facts
- diagnostics / governance tooling that intentionally audits native exposure

`native_projection` should **not** remain the default capability source for
ordinary `system.init` requests in steady state.

### C. Materialization boundary

Capability registry should be materialized **before** ordinary `system.init`
request assembly.

Acceptable materialization locations include:

- startup/bootstrap preparation
- dedicated registry build / refresh flow
- cached shared-service layer owned by platform kernel
- explicit governance rebuild path with version/invalidation semantics

The key rule is:

> `system.init` may consume a materialized capability registry, but it should
> not be the place where broad native capability discovery is continuously
> re-executed as normal startup behavior.

## Practical Consequence

This recovery decision changes the next engineering question.

The next question is no longer:

- "Which native adapter should be optimized next?"

The next question becomes:

- "How does the platform kernel materialize and invalidate capability registry
  facts, and how is `system.init` restricted to consuming that materialized
  result?"

## Recommended Next Batch

Open a dedicated design/screen batch for:

- capability registry materialization path
- fallback gating rules
- invalidation/version semantics
- `system.init` mainline consumption contract

That batch should produce a concrete implementation direction for replacing the
current request-time mixed ownership model.
