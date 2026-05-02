# Unified Semantic Page Contract Lite - Phase 2 Candidate Plan Batch 37

Date: 2026-05-02
Status: planning only

## 1. Boundary

Layer Target: Contract Governance / Lite Phase 2 Candidate Planning

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Phase 1 is closed as `ready_for_phase2_planning`. Phase 2 must not start by
opening multiple runtime entries. This batch selects the next candidate and
freezes the implementation gate that must exist before any code change.

This document is not approved for implementation.

## 2. Candidate Decision

Recommended candidate:

```text
load_contract opt-in preview
```

Candidate boundary:

```text
backend-only preview, no frontend consumption
```

Decision:

```text
phase2_candidate_selected_planning_only
```

## 3. Why This Candidate

`api_onchange` already proves patch-style Lite output can be added without
changing legacy behavior. The next useful boundary is page contract assembly,
but it must be tested without page-load default changes and without frontend
runtime consumption.

`load_contract` is the lowest useful next candidate because:

- it is closer to page contract assembly than `api_onchange`
- it can remain explicit opt-in only
- default page load behavior can remain unchanged
- it can be validated through handler and HTTP smoke before frontend adoption
- rollback remains one-step: disable the opt-in branch

## 4. Rejected For This Phase

Rejected:

```text
ui.contract
frontend runtime
system.init
login
runtimeContract
```

Reasons:

- `ui.contract` is closer to startup/page delivery and carries higher surface risk
- frontend runtime consumption would turn preview into product behavior
- `system.init` and `login` must remain pure startup-chain contracts
- `runtimeContract` belongs to the rejected heavy runtime direction

## 5. Required Phase 2 Implementation Shape

Before implementation, the next batch must declare:

```text
Layer Target:
Module:
Reason:
Entry Point: load_contract
Opt-in Flag:
Default Behavior:
Response Field:
Rollback:
Positive Validation:
Negative Validation:
Frontend Boundary:
```

Required rules:

- default `load_contract` response remains unchanged
- Lite preview requires explicit opt-in
- response field must not be consumed by frontend
- no `ui.contract` change
- no `system.init` change
- no `login` change
- no frontend runtime change
- no `runtimeContract`

## 6. Required Verification For Implementation Batch

The implementation batch must add and pass:

```bash
make verify.unified_page_contract.lite
make verify.unified_page_contract.lite.load_contract_preview_interface
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
make verify.unified_page_contract.lite.frontend_runtime_negative
make verify.contract.preflight
make verify.boundary.guard
make verify.frontend.quick.gate
```

The implementation batch must keep this existing negative guard green:

```bash
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
```

until the new opt-in preview behavior has its own explicit positive guard.

## 7. Stop Conditions

Stop immediately if any implementation plan requires:

- default `load_contract` shape change
- frontend consumption of `lite_preview`
- `ui.contract` propagation
- startup-chain propagation
- broad runtime kernel
- schema expansion into `runtimeContract`

## 8. Rollback

Rollback must be:

```text
disable load_contract opt-in preview branch
```

Rollback must not require:

- database migration
- frontend deployment
- public intent rename
- user data cleanup

## 9. Next Step

The next allowed batch is still planning-to-implementation preparation:

```text
load_contract opt-in preview implementation gate design
```

No implementation may start until the gate defines the exact opt-in request
shape, response field, positive smoke, negative smoke, and rollback.
