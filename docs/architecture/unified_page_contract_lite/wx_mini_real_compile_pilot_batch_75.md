# Unified Semantic Page Contract Lite - wx_mini Real Compile Pilot Batch 75

Date: 2026-05-03
Status: guarded, dependency-blocked

## 1. Boundary

Layer Target: Frontend Mobile Compile Verification

Module:

- `frontend/apps/mobile`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

The wx_mini workspace and compile script now exist, but this is not the same as
a successful mini-program compile. This batch adds a real compile pilot gate that
does not install dependencies implicitly and does not report success until the
lockfile, installed dependencies, and actual build command are all present.

## 2. Guarded Target

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
```

The target runs:

```bash
python3 scripts/verify/unified_page_contract_lite_wx_mini_real_compile_pilot_guard.py \
  --report artifacts/backend/unified_page_contract_lite_wx_mini_real_compile_pilot.json
```

## 3. Current Decision

```text
wx_mini_real_compile_pilot_blocked_missing_lockfile_or_dependencies
```

This means:

- `frontend/apps/mobile/package.json` exists
- `frontend/apps/mobile/src/manifest.json` exists
- `build:mp-weixin` exists
- `pnpm` is available
- the frontend lockfile does not yet contain the mobile UniApp dependency graph
- mobile dependencies are not installed
- the real `pnpm -C frontend/apps/mobile build:mp-weixin` command has not run

## 4. Non-Goals

This batch does not:

- run `pnpm install`
- update `pnpm-lock.yaml`
- download UniApp dependencies
- execute the real mini-program compile
- mark wx_mini as terminal-covered
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Next Gate

The next executable step is dependency lock/install:

```bash
pnpm -C frontend install
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
```

After dependencies are present, the guard can be run with `--execute` by a
dedicated Make target in the next batch to perform the real build command.

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this compile pilot guard batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
