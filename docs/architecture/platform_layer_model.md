# Platform Layer Model (R4)

## Purpose

Define the Smart Core platform layering and the non-intrusion boundary for industry expansion.

R4 baseline question:

- Is this an engineering system tied to one domain?
- Or a reusable industry platform kernel?

This document sets the architectural contract for that answer.

## Layering

### L0: Platform Kernel (immutable during industry expansion)

Scope:

- Intent kernel and routing:
  - `addons/smart_core/core/intent_router.py`
  - `addons/smart_core/core/base_handler.py`
  - `addons/smart_core/core/handler_registry.py`
- Contract runtime and orchestration:
  - `addons/smart_core/handlers/system_init.py`
  - scene runtime pipeline components under `addons/smart_core/core/`
- Contract envelope and governance guards:
  - `scripts/verify/*` kernel/security guards

Rules:

- No industry-specific model, role, or scene semantics may be hardcoded in L0.
- L0 changes are only allowed for generic kernel capability evolution.
- Industry onboarding must not require modifying L0 files.

### L1: Industry Domain Layer (replaceable/extendable)

Scope:

- Industry addon modules, for example:
  - `addons/smart_construction_core`
  - `addons/smart_owner_core` (R4 simulation)
  - future `addons/smart_medical_core`
- Domain intents, capability definitions, scene definitions, domain services.

Rules:

- Register intents through extension hook (`smart_core_register`).
- Extend `system.init` only through extension hook (`smart_core_extend_system_init`).
- Do not patch L0 handler/router code directly.

### L2: Organization Policy Layer (composable)

Scope:

- Permission matrix and role composition.
- Capability packaging and scene composition strategy.
- Runtime policy and governance gates.

Rules:

- Organization policy should recompose L1 behavior without changing L0.
- Policy changes must be guard-verifiable via `make verify.platform.kernel.ready`.

## Non-Intrusion Contract

Industry extension is valid only when all are true:

1. L0 files unchanged.
2. New intents added by extension registration only.
3. New capabilities/scenes introduced in industry module.
4. Existing kernel gates still pass (`verify.platform.kernel.ready`).

## R4 Verification Mapping

- R4-01: this document.
- R4-02/R4-03: owner module added with extension-only registration, no L0 edits.
- R4-04: capability isolation report (construction vs owner namespaces).
- R4-05: owner scene-only deployment simulation report and system.init stability check.

