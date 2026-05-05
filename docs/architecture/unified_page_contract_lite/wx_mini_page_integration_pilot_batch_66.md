# Unified Semantic Page Contract Lite - wx_mini Page Integration Pilot Batch 66

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Page Integration Pilot

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

wx_mini already has shared renderer output readiness. The next step is to prove
that renderer output can be wrapped into a page integration shape without a
wx_mini-specific contract, route dependency, request dependency, or frontend
business semantics.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `wx_mini`
- builds renderer output from the same shared renderer path
- builds a page integration snapshot from renderer output
- verifies root node, mounted node count, and readiness
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared page integration path

## 3. Current Decision

```text
wx_mini_page_integration_pilot_ready_runtime_mount_pending
```

This means:

- wx_mini can enter the shared contract consumer path
- wx_mini can produce shared renderer input
- wx_mini can produce shared renderer output
- wx_mini can produce a page integration shape
- real runtime mount and mini-program compilation are still pending

## 4. Non-Goals

This batch does not:

- implement a UniApp page
- compile a mini program
- mount in a real runtime
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this page integration pilot batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
