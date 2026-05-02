# Unified Semantic Page Contract Lite - Phase 2 load_contract Gate Batch 38

Date: 2026-05-02
Status: implementation gate design only

## 1. Boundary

Layer Target: Contract Governance / Lite load_contract Implementation Gate Design

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch 37 selected `load_contract opt-in preview` as the Phase 2 candidate. This
batch defines the exact implementation gate that must exist before any
`load_contract` Lite preview code is added.

This document is not approved for implementation.

## 2. Entry Point

Entry point:

```text
load_contract
```

Handler:

```text
addons/smart_core/handlers/load_contract.py
```

Mode:

```text
backend-only preview
```

Frontend consumption:

```text
not allowed
```

## 3. Opt-In Request Shape

The only valid preview opt-in request shape is:

```json
{
  "intent": "load_contract",
  "params": {
    "model": "project.project",
    "view_type": "tree",
    "include": "all",
    "contractMode": "lite_preview",
    "contractVersion": "2.0.0",
    "entryPoint": "load_contract",
    "clientType": "web_pc",
    "fallbackMode": "legacy_default",
    "traceId": "lite-load-contract-preview-001"
  }
}
```

Missing or invalid opt-in fields must keep legacy behavior.

## 4. Response Field

The only allowed preview field is top-level:

```text
lite_preview
```

Allowed payload type:

```text
lite_contract
```

Required response behavior:

- legacy `status` remains unchanged
- legacy `code` remains unchanged
- legacy `data` remains unchanged
- legacy `meta` remains unchanged except existing normal metadata behavior
- valid opt-in may add top-level `lite_preview`
- invalid opt-in must not add `lite_preview`
- default request must not add `lite_preview`

## 5. Positive Guard Required Before Implementation Closure

The implementation batch must add:

```bash
make verify.unified_page_contract.lite.load_contract_preview_interface
```

Required assertions:

- default handler call has no `lite_preview`
- incomplete opt-in has no `lite_preview`
- valid opt-in has top-level `lite_preview`
- valid opt-in has `payloadType=lite_contract`
- valid opt-in keeps legacy `data` unchanged

The implementation batch must also add:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container
```

Required assertions:

- HTTP login works
- valid load_contract opt-in returns top-level `lite_preview`
- `lite_preview.payloadType` is `lite_contract`
- legacy `data` remains present and unchanged
- response does not require frontend runtime consumption

## 6. Negative Guard Required Before Implementation Closure

The existing negative smoke:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
```

must be split or narrowed during implementation so it asserts only:

- default request has no `lite_preview`
- incomplete opt-in has no `lite_preview`
- wrong `entryPoint` has no `lite_preview`
- wrong `contractVersion` has no `lite_preview`

After the positive preview guard exists, this negative guard must not send a
fully valid `load_contract` opt-in and expect no preview.

## 7. Frontend Boundary

Frontend must remain unchanged.

Required guard:

```bash
make verify.unified_page_contract.lite.frontend_runtime_negative
```

Forbidden frontend tokens remain:

```text
lite_preview
payloadType
lite_contract
runtimeContract
UnifiedPageContractLite
unified_page_contract_lite
```

## 8. Startup Boundary

Startup chain must remain unchanged.

Required guard:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
```

No `login`, `system.init`, or `ui.contract` response may expose Lite preview.

## 9. Required Batch Closure Gates

An implementation batch cannot close unless all pass:

```bash
make verify.unified_page_contract.lite
make verify.unified_page_contract.lite.load_contract_preview_interface
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.unified_page_contract.lite.frontend_runtime_negative
make verify.contract.preflight
make verify.boundary.guard
make verify.frontend.quick.gate
make verify.docs.all
git diff --check
```

## 10. Rollback

Rollback:

```text
disable load_contract opt-in preview branch
```

Rollback must not require:

- database migration
- frontend deployment
- public intent rename
- user data cleanup

## 11. Stop Conditions

Stop implementation if it requires:

- changing default `load_contract` response
- moving Lite preview into `data`
- frontend consumption
- `ui.contract` propagation
- startup-chain propagation
- `runtimeContract`
- component registry
- dependency graph
- selector status
- realtime or streaming behavior
