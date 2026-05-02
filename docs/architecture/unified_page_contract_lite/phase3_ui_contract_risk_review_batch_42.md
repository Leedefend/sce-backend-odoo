# Unified Semantic Page Contract Lite - Phase 3 ui.contract Risk Review Batch 42

Date: 2026-05-02
Status: risk review only

## 1. Boundary

Layer Target: Contract Governance / Lite ui.contract Risk Review

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

`api_onchange` and `load_contract` now have explicit opt-in preview coverage.
Before selecting the next runtime entry, `ui.contract` must be reviewed because
it sits closer to startup and frontend delivery than `load_contract`.

This document is not approved for implementation.

## 2. Risk Decision

Decision:

```text
ui_contract_not_ready_for_runtime_preview
```

Reason:

```text
ui.contract is a frontend delivery surface and must not become the next Lite runtime entry before a controlled frontend pilot gate exists.
```

## 3. Current Allowed Entries

Allowed explicit opt-in preview entries:

```text
api_onchange
load_contract
```

Still blocked:

```text
ui.contract
login
system.init
frontend runtime
runtimeContract
```

## 4. Why ui.contract Is Higher Risk

`ui.contract` is not just a backend handler boundary. It is connected to page
delivery and frontend contract consumption. Opening it before a frontend pilot
gate would blur these guarantees:

- default frontend delivery remains legacy
- startup chain remains Lite-free
- frontend runtime does not consume `lite_preview`
- rollback is still one-step
- user-visible page behavior is unchanged

## 5. Required Prerequisite Before ui.contract Candidate

Before `ui.contract` can be considered as a candidate, a separate batch must
define:

```text
Frontend Controlled Pilot Gate
```

That gate must include:

- exact pilot page or model
- exact frontend feature flag
- legacy fallback path
- rollback command or config
- default-off behavior
- browser smoke
- startup negative guard
- frontend negative guard for non-pilot paths
- no `runtimeContract`

## 6. Stop Conditions

Stop immediately if a plan requires:

- default `ui.contract` response change
- `login` or `system.init` propagation
- global frontend runtime consumption
- removing legacy fallback
- making Lite the default page contract
- adding `runtimeContract`
- introducing selector status, dependency graph, realtime, or streaming

## 7. Recommended Next Candidate

Recommended next step:

```text
frontend controlled pilot readiness design
```

Not recommended now:

```text
ui.contract opt-in preview implementation
```

## 8. Required Guards

This risk decision must remain guarded by:

```bash
make verify.unified_page_contract.lite
make verify.unified_page_contract.lite.load_contract_live_scope.container
make verify.unified_page_contract.lite.frontend_runtime_negative
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.contract.preflight
make verify.boundary.guard
make verify.frontend.quick.gate
```

## 9. Rollback

No runtime change is made by this batch.

Rollback:

```text
remove this risk review document and guard
```
