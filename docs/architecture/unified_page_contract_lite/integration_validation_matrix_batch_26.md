# Unified Semantic Page Contract Lite - Integration Validation Matrix Batch 26

Date: 2026-05-02
Status: validation matrix only

## 1. Boundary

Layer Target: Contract Governance / Integration Verification Matrix

Module:

- `docs/architecture/unified_page_contract_lite`
- `scripts/verify`
- `Makefile`

Reason:

Batch-25 proved that the demo business closure can run through real browser approval paths. Batch-26 freezes the matrix that future Lite preview integration must satisfy before expanding beyond `api.onchange`.

This document is not a runtime implementation.

## 2. Runtime Scope

Allowed current runtime entry:

```text
api_onchange
```

Blocked runtime entries:

```text
load_contract
ui_contract
login
system_init
frontend_runtime
```

The matrix must keep `legacy_default` behavior unchanged unless the request explicitly opts in with `contractMode=lite_preview`.

## 3. Required Demo Business Matrix

The integration baseline must cover these 14 models through real browser approval and backend assertion:

| Index | Model | Expected closure |
| --- | --- | --- |
| 0 | `construction.contract` | approved and removed from todo |
| 1 | `sc.general.contract` | approved and removed from todo |
| 2 | `sc.legacy.purchase.contract.fact` | approved and removed from todo |
| 3 | `payment.request` | approved and removed from todo |
| 4 | `sc.expense.claim` | approved and removed from todo |
| 5 | `project.material.plan` | approved and removed from todo |
| 6 | `sc.settlement.order` | approved and removed from todo |
| 7 | `purchase.order` | approved and removed from todo |
| 8 | `sc.receipt.income` | approved and removed from todo |
| 9 | `sc.payment.execution` | approved and removed from todo |
| 10 | `sc.invoice.registration` | approved and removed from todo |
| 11 | `sc.financing.loan` | approved and removed from todo |
| 12 | `sc.treasury.reconciliation` | approved and removed from todo |
| 13 | `sc.settlement.adjustment` | approved and removed from todo |

Required segmented command set:

```bash
BROWSER_CLOSURE_CASE_OFFSET=0 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=2 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=4 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=6 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=8 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=10 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
BROWSER_CLOSURE_CASE_OFFSET=12 BROWSER_CLOSURE_CASE_LIMIT=2 make verify.portal.business_real_user_browser_closure
```

Each segment must prove:

- browser login with the assigned reviewer
- native action dispatch reaches `execute_button`
- confirmation dialog is accepted
- record is approved
- record is removed from the reviewer todo list
- backend state matches the expected state
- `validation_status` is `validated` when the model provides it
- `tier.review` status is `approved`
- cleanup succeeds

## 4. Required Lite Preview Matrix

The `api_onchange` Lite preview path must keep these cases stable:

| Case | Request | Expected result |
| --- | --- | --- |
| default onchange | no `contractMode` | unchanged legacy response |
| incomplete opt-in | missing `contractVersion` | unchanged legacy response |
| valid opt-in | full `lite_preview` envelope | top-level `lite_preview` only |
| valid opt-in payload | `entryPoint=api_onchange` | `payloadType=lite_patch` |
| legacy data | any valid opt-in | legacy `data` remains unchanged |
| handler boundary | Odoo shell `ApiOnchangeHandler` | same default / incomplete / valid opt-in behavior |

Required guard:

```bash
make verify.unified_page_contract.lite
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_live_scope.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_live_scope.container
DB_NAME=sc_demo make verify.unified_page_contract.lite.api_onchange_interface
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.api_onchange_intent.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.startup_negative.container
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_negative.container
DB_NAME=sc_demo make verify.unified_page_contract.lite.load_contract_preview_interface
DB_NAME=sc_demo E2E_LOGIN=cost1 E2E_PASSWORD=123456 make verify.unified_page_contract.lite.load_contract_preview_intent.container
make verify.unified_page_contract.lite.frontend_runtime_negative
```

## 5. Required Contract And Frontend Gates

Before any broader runtime connection, these gates must pass:

```bash
make verify.contract.preflight
make verify.boundary.guard
make verify.frontend.quick.gate
make verify.docs.all
git diff --check
```

For runtime smoke with demo data, these gates must pass:

```bash
make verify.portal.execute_button_smoke.container
make verify.portal.envelope_smoke.container
make verify.portal.view_contract_coverage_smoke.container
make verify.portal.view_contract_shape.container
make verify.portal.view_render_mode_smoke.container
```

Service trust must be checked with:

```bash
make ps
```

## 6. Forbidden Expansion

Batch-26 does not approve:

- enable Lite preview by default
- change `login`
- change `system.init`
- change `ui.contract`
- change `load_contract`
- change frontend runtime
- introduce `runtimeContract`
- add component registry
- add dependency graph
- add selector status
- add realtime or streaming behavior

## 7. Decision Rule

The next runtime batch may proceed only if:

- all 14 demo business matrix entries are green
- `make verify.unified_page_contract.lite` is green
- contract, boundary, frontend, docs, and diff gates are green
- services are healthy
- rollback remains `disable opt-in flag`

If any item fails, the next batch must stop and classify the failure as one of:

- `CODE_ERROR`
- `CONTRACT_MISMATCH`
- `CONTRACT_MISSING`
- `ENV_UNSTABLE`
- `GUARD_FAIL`
- `SNAPSHOT_DIFF`

## 8. Next Allowed Batch

The next allowed implementation batch is still limited to:

```text
api.onchange Lite opt-in preview validation and evidence hardening
```

It is not approval to expand Lite runtime to page load, `ui.contract`, or frontend consumption.
