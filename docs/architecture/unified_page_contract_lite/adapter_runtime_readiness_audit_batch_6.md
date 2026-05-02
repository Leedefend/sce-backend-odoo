# Unified Semantic Page Contract Lite - Adapter Runtime Readiness Audit Batch 6

Date: 2026-05-02
Status: Phase 1 runtime readiness audit, not connected

## 1. Boundary

Layer Target: Contract Governance / Runtime Readiness Audit

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch-5 proved Lite patch semantics for form/tree/search and x2many row status/data separation. Batch-6 freezes the runtime boundary before any connection work:

```text
adapter may exist
adapter must remain offline
runtime insertion must be a later explicit batch
```

## 2. Current Connection Status

Current status:

```text
not connected
```

The Lite adapter is currently allowed only as:

- pure backend transformer source
- static fixture/snapshot generator
- guard target
- architecture documentation subject

It must not be imported or called by:

- public intent handlers
- controllers
- Odoo models
- frontend runtime/store/renderer
- startup chain delivery code

## 3. Candidate Future Insertion Points

These are only candidates. They are not active in this batch.

### `load_contract`

Candidate:

```text
addons/smart_core/handlers/load_contract.py
```

Potential insertion point:

```text
after native/semantic page data has been shaped
before optional projected delivery is returned
```

Required rule:

```text
legacy/default delivery remains unchanged unless an explicit opt-in flag is introduced
```

### `ui_contract`

Candidate:

```text
addons/smart_core/handlers/ui_contract.py
```

Potential insertion point:

```text
after final projected contract is built
behind a non-default Lite contract request mode
```

Required rule:

```text
login -> system.init -> ui.contract default output must not drift
```

### `api.onchange`

Candidate:

```text
existing onchange response wrapper
```

Potential insertion point:

```text
map onchange/modifiers/x2many deltas into Lite partial patch
```

Required rule:

```text
data deltas and status deltas stay separated
```

## 4. Must Not Touch Before Integration Batch

Batch-6 and any audit-only batch must not modify:

- `login`
- `system.init`
- `ui.contract` default output
- public intent names
- handler default return shape
- frontend runtime
- frontend contract store
- frontend renderer
- Odoo model registration
- controller routes
- security/access CSV
- `runtimeContract`

## 5. Future Integration Gates

Before any future runtime connection is allowed, the batch must pass:

```bash
make verify.unified_page_contract.lite
make verify.native_view.semantic_page
make verify.frontend.onchange_contract_schema.guard
make verify.frontend.onchange_roundtrip.guard
make verify.frontend.x2many_command_semantic.guard
```

If the future batch touches delivery or startup chain, it must also add targeted startup-chain verification for:

```text
login -> system.init -> ui.contract
```

## 6. New Boundary Guard

Batch-6 adds:

```text
scripts/verify/unified_page_contract_lite_runtime_boundary_guard.py
```

The guard scans repository text files for:

- `unified_page_contract_lite_adapter`
- `build_lite_contract`
- `build_lite_patch`

Allowed references:

- adapter implementation
- adapter guard
- runtime boundary guard
- Lite architecture docs
- iteration log
- `Makefile`

Forbidden references include:

- `addons/smart_core/handlers/`
- `addons/smart_core/controllers/`
- `addons/smart_core/models/`
- `frontend/`

Report:

```text
artifacts/backend/unified_page_contract_lite_runtime_boundary.json
```

## 7. Decision

Batch-6 decision:

```text
Lite adapter is runtime-ready only as an audited offline component.
Runtime integration remains blocked until a dedicated integration batch is opened.
```
