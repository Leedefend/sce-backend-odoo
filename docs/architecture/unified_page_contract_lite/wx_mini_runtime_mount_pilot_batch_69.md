# Unified Semantic Page Contract Lite - wx_mini Runtime Mount Pilot Batch 69

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Runtime Mount Pilot

Module:

- `frontend/apps/web/src/app/contracts`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

wx_mini already has page integration readiness. The next step is to prove that
the page integration shape can enter a minimal runtime mount state without
creating a wx_mini-specific runtime, route dependency, request dependency, or
frontend business semantics.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `wx_mini`
- builds a page integration shape from the same shared path
- builds a runtime mount snapshot from page integration
- verifies root node, mounted node count, and mounted status
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared runtime mount path

## 3. Current Decision

```text
wx_mini_runtime_mount_pilot_ready_compile_pending
```

This means:

- wx_mini can enter the shared contract consumer path
- wx_mini can produce shared renderer input
- wx_mini can produce shared renderer output
- wx_mini can produce page integration shape
- wx_mini can produce runtime mount state
- real mini-program compilation and device/runtime smoke are still pending

## 4. Non-Goals

This batch does not:

- implement a UniApp page
- compile a mini program
- start a mini-program runtime
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this runtime mount pilot batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
