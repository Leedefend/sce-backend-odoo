# Unified Semantic Page Contract Lite - wx_mini Renderer Input Pilot Batch 60

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Verification / All-Terminal Coverage

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

The first wx_mini step must prove the shared Lite store and renderer input path
can accept a wx_mini contract without creating a mini-program-specific contract.
This is not yet a UniApp page rendering test.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `wx_mini`
- creates the same terminal boundary shape
- creates the same terminal renderer input shape
- verifies widget, field, and action counts
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared store/input path

## 3. Current Decision

```text
wx_mini_renderer_input_ready_ui_renderer_pending
```

This means:

- wx_mini can enter the shared contract consumer path
- wx_mini can produce shared renderer input
- wx_mini UI rendering is still pending

## 4. Non-Goals

This batch does not:

- implement UniApp UI
- compile a mini program
- render a wx_mini page
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_renderer_input_pilot.host
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this pilot guard batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
