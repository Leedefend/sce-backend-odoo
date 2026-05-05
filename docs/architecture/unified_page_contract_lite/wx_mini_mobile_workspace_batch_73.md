# Unified Semantic Page Contract Lite - wx_mini Mobile Workspace Batch 73

Date: 2026-05-03
Status: implemented workspace skeleton

## 1. Boundary

Layer Target: Frontend Mobile Workspace / Compile Preflight

Module:

- `frontend/apps/mobile`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`

Reason:

The wx_mini compile preflight proved the repository did not have a UniApp mobile
workspace. This batch adds the minimum workspace shape required for the compile
pilot to move from missing workspace to compile-ready preflight.

## 2. What This Batch Adds

This batch adds:

```text
frontend/apps/mobile/package.json
frontend/apps/mobile/src/manifest.json
frontend/apps/mobile/src/pages.json
frontend/apps/mobile/src/App.vue
frontend/apps/mobile/src/main.ts
frontend/apps/mobile/src/pages/contract/index.vue
frontend/apps/mobile/tsconfig.json
```

The mobile package declares:

```bash
pnpm -C frontend/apps/mobile build:mp-weixin
```

## 3. Current Decision

```text
wx_mini_compile_pilot_ready
```

This means:

- the UniApp workspace entry exists
- the mini-program build script is declared
- real dependency installation and compile execution are still pending

## 4. Non-Goals

This batch does not:

- install UniApp dependencies
- compile a mini program
- start a mini-program runtime
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this mobile workspace skeleton batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
