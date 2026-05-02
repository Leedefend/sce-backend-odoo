# Unified Semantic Page Contract Lite - Runtime Integration Plan Batch 14

Date: 2026-05-02
Status: integration planning only

## 1. Boundary

Layer Target: Contract Governance / Runtime Integration Planning Gate

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Phase 1 readiness is now machine-gated. This batch defines the only acceptable path for a future runtime integration batch.

This document is a plan, not an implementation.

## 2. Non-Negotiable Rules

The future runtime integration must be:

- opt-in only
- non-default
- reversible
- guarded by startup-chain verification
- limited to one runtime entry point per batch

The future runtime integration must not change:

- `login`
- `system.init`
- default `ui.contract` output
- public intent names
- default route semantics
- frontend runtime behavior
- `runtimeContract`

## 3. Allowed Future Entry Points

Only one of these may be opened in a future batch:

### Option A: `load_contract` opt-in preview

Candidate:

```text
addons/smart_core/handlers/load_contract.py
```

Rule:

```text
default response remains unchanged
Lite output requires explicit opt-in flag
```

### Option B: `ui_contract` opt-in preview

Candidate:

```text
addons/smart_core/handlers/ui_contract.py
```

Rule:

```text
default ui.contract remains unchanged
Lite output requires explicit opt-in flag
```

### Option C: `api.onchange` opt-in patch preview

Candidate:

```text
existing onchange response wrapper
```

Rule:

```text
default onchange response remains unchanged
Lite patch requires explicit opt-in flag
```

## 4. Required Future Batch Shape

Any future runtime integration batch must declare:

```text
Layer Target:
Module:
Reason:
Entry Point:
Opt-in Flag:
Default Behavior:
Rollback:
Verification:
```

## 5. Required Verification

Future integration must pass:

```bash
make verify.unified_page_contract.lite
make verify.native_view.semantic_page
make verify.frontend.onchange_contract_schema.guard
make verify.frontend.onchange_roundtrip.guard
make verify.frontend.x2many_command_semantic.guard
```

If touching delivery or startup chain, it must also add targeted startup-chain proof for:

```text
login -> system.init -> ui.contract
```

## 6. Rollback Rule

Rollback must be one-step:

```text
disable opt-in flag
```

No database migration, frontend deployment, or public intent rename may be required to return to current behavior.

## 7. Decision

Runtime integration is not approved by this batch.

This batch only creates a governed planning gate for a future explicit integration batch.
