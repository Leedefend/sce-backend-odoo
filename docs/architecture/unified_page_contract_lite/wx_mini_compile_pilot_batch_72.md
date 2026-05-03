# Unified Semantic Page Contract Lite - wx_mini Compile Pilot Batch 72

Date: 2026-05-03
Status: implemented preflight guard

## 1. Boundary

Layer Target: Frontend Contract Consumer / Compile Preflight

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

wx_mini already has runtime mount readiness, but the repository does not yet
contain a UniApp mini-program workspace. The compile pilot must report this
truthfully instead of marking wx_mini as compiled.

## 2. What This Batch Adds

This batch adds:

```bash
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
```

The guard verifies:

- the current web package still exists
- whether `frontend/apps/mobile/package.json` exists
- whether `frontend/apps/mobile/src/manifest.json` exists
- whether the Makefile exposes the compile pilot target
- the required future compile script name is `build:mp-weixin`

## 3. Current Decision

```text
wx_mini_compile_pilot_blocked_missing_uniapp_workspace
```

This means:

- wx_mini contract/render/page/runtime mount readiness is present
- real mini-program compilation is not ready
- the next implementation batch must create the UniApp mobile workspace

## 4. Required Next Workspace

The minimum expected workspace is:

```text
frontend/apps/mobile/package.json
frontend/apps/mobile/src/manifest.json
build:mp-weixin
```

## 5. Non-Goals

This batch does not:

- create the UniApp workspace
- install dependencies
- compile a mini program
- start a mini-program runtime
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this compile preflight batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
