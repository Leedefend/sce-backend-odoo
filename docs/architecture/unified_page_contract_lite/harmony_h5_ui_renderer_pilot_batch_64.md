# Unified Semantic Page Contract Lite - harmony_h5 UI Renderer Pilot Batch 64

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Renderer Pilot

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

harmony_h5 must reuse the same shared terminal renderer output path as wx_mini.
This proves H5 rendering readiness without creating a Harmony-specific contract
or adding frontend business logic.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `harmony_h5`
- builds renderer input from the same Lite terminal boundary
- builds renderer output nodes from widget/action identifiers
- verifies field and action node counts
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared renderer path

## 3. Current Decision

```text
harmony_h5_ui_renderer_pilot_ready_page_integration_pending
```

This means:

- harmony_h5 can enter the shared contract consumer path
- harmony_h5 can produce shared renderer input
- harmony_h5 can produce shared renderer output
- real H5 page integration is still pending

## 4. Non-Goals

This batch does not:

- implement a Harmony H5 page
- compile a UniApp H5 app
- mount renderer output in a real page
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host
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
