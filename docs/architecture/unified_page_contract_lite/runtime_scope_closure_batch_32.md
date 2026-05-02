# Unified Semantic Page Contract Lite - Runtime Scope Closure Batch 32

Date: 2026-05-02
Status: scope closure guard

## 1. Boundary

Layer Target: Contract Governance / Lite Runtime Scope Closure

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

The current implementation has enough evidence to start controlled validation,
but only for the explicit `api_onchange` Lite preview path. This batch freezes
that boundary as a single guard so later batches do not mistake scattered
positive evidence for broad runtime approval.

This document is not approval to expand Lite runtime to page load, `ui.contract`,
startup chain, or frontend consumption.

Phase 2 update: Batch 39 later added `load_contract opt-in preview` as a
backend-only preview entry. This still does not approve `ui.contract`, startup
chain, or frontend runtime consumption.

## 2. Current Allowed Runtime Entry

Allowed:

```text
api_onchange
load_contract opt-in preview
```

The allowed behavior is still opt-in only:

- no `contractMode=lite_preview` means unchanged legacy response
- incomplete opt-in means unchanged legacy response
- valid opt-in may add top-level `lite_preview`
- valid opt-in keeps legacy `data` unchanged
- valid `api_onchange` opt-in payload type is `lite_patch`
- valid `load_contract` opt-in payload type is `lite_contract`

## 3. Blocked Runtime Entries

Blocked:

```text
ui_contract
login
system_init
frontend_runtime
```

The blocked entries must not expose `lite_preview`, `payloadType=lite_patch`, or
any frontend runtime consumption path until a separate owner-approved batch
changes the scope.

## 4. Evidence Map

Positive `api_onchange` evidence:

- `api_onchange_preview_behavior_batch_20.md`
- `api_onchange_preview_interface_batch_27.md`
- `api_onchange_preview_intent_smoke_batch_28.md`

Negative scope evidence:

- `startup_chain_negative_smoke_batch_29.md`
- `load_contract_negative_smoke_batch_30.md`
- `frontend_runtime_negative_batch_31.md`

Matrix evidence:

- `integration_validation_matrix_batch_26.md`

## 5. Guard

Required static closure guard:

```bash
make verify.unified_page_contract.lite.runtime_scope_closure
```

Required live scope aggregate guard:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_live_scope.container
```

Required aggregate guard:

```bash
make verify.unified_page_contract.lite
```

The closure guard checks that:

- all positive and negative evidence docs exist
- all supporting verify scripts exist
- the Makefile exposes the current positive, negative, and aggregate live scope targets
- Phase 1 readiness includes the runtime scope closure evidence
- the integration matrix still lists `api_onchange` as the only allowed runtime entry
- the integration matrix still lists all blocked runtime entries
- no approval phrase exists for broader runtime expansion

## 6. Forbidden Expansion

This batch still forbids:

- enabling Lite preview by default
- changing `login`
- changing `system.init`
- changing `ui.contract`
- changing `load_contract`
- changing frontend runtime consumption
- introducing `runtimeContract`
- introducing component registry
- introducing dependency graph
- introducing selector status
- introducing realtime or streaming behavior

## 7. Decision

The current runtime scope is closed as:

```text
runtime_scope_closed_api_onchange_only
```

Next validation may continue only inside the `api_onchange` opt-in preview
boundary. Any expansion to page-load contract, startup chain, frontend renderer,
or runtimeContract requires a new bounded batch with its own design, guard, and
rollback.
