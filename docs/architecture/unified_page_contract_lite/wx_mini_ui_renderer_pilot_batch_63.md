# Unified Semantic Page Contract Lite - wx_mini UI Renderer Pilot Batch 63

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Renderer Pilot

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

wx_mini already has renderer input readiness. The next step is to prove that
the shared terminal renderer can turn that input into a renderable output shape
without creating a wx_mini-specific contract or adding frontend business logic.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `wx_mini`
- builds renderer input from the same Lite terminal boundary
- builds renderer output nodes from widget/action identifiers
- verifies field and action node counts
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared renderer path

## 3. Current Decision

```text
wx_mini_ui_renderer_pilot_ready_page_integration_pending
```

This means:

- wx_mini can enter the shared contract consumer path
- wx_mini can produce shared renderer input
- wx_mini can produce shared renderer output
- real UniApp page integration is still pending

## 4. Non-Goals

This batch does not:

- implement a UniApp page
- compile a mini program
- mount renderer output in a real page
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this UI renderer pilot batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
