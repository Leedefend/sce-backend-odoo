# Unified Semantic Page Contract Lite - harmony_h5 Runtime Mount Pilot Batch 70

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Runtime Mount Pilot

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

harmony_h5 must reuse the same shared runtime mount state as wx_mini. This keeps
H5 on the same terminal contract path and avoids a Harmony-specific runtime,
route dependency, request dependency, or frontend business semantics.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host
```

The guard:

- loads the project tree Lite contract snapshot
- switches only `pageInfo.clientType` to `harmony_h5`
- builds a page integration shape from the same shared path
- builds a runtime mount snapshot from page integration
- verifies root node, mounted node count, and mounted status
- verifies no role, permission, route, capability, request, or JSON-RPC logic is
  present in the shared runtime mount path

## 3. Current Decision

```text
harmony_h5_runtime_mount_pilot_ready_compile_pending
```

This means:

- harmony_h5 can enter the shared contract consumer path
- harmony_h5 can produce shared renderer input
- harmony_h5 can produce shared renderer output
- harmony_h5 can produce page integration shape
- harmony_h5 can produce runtime mount state
- real H5 compilation and runtime smoke are still pending

## 4. Non-Goals

This batch does not:

- implement a Harmony H5 page
- compile a UniApp H5 app
- start a real H5 runtime
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host
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
