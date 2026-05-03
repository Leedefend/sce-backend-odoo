# Unified Semantic Page Contract Lite - wx_mini Real Compile Pass Batch 76

Date: 2026-05-03
Status: real compile passed

## 1. Boundary

Layer Target: Frontend Mobile Compile Verification

Module:

- `frontend/apps/mobile`
- `frontend/pnpm-lock.yaml`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

The previous gate proved the repository had a mobile workspace but lacked a
locked and installed UniApp dependency graph. This batch locks the real UniApp
Vue3 dependency line, installs local dependencies for verification, and proves
the wx_mini package can compile.

## 2. What Changed

This batch adds or fixes:

```text
frontend/apps/mobile/index.html
frontend/apps/mobile/vite.config.ts
frontend/apps/mobile/package.json
frontend/pnpm-lock.yaml
```

The mobile package now uses the DCloud Vue3 dist-tag line:

```text
3.0.0-alpha-5000820260430001
```

The package also includes:

```text
@dcloudio/uni-mp-weixin
vite@5.2.8
```

## 3. Current Decision

```text
wx_mini_real_compile_pilot_passed
```

The compile output is generated locally under:

```text
frontend/apps/mobile/dist/build/mp-weixin
```

Generated build output and `node_modules` are local verification artifacts and
are not committed.

## 4. Non-Goals

This batch does not:

- run a WeChat developer tool simulator
- perform device acceptance
- connect a live backend from the mini-program runtime
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Next Gate

Next executable gate:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
```

That gate should prove the compiled terminal can load the contract renderer
surface without treating the compile artifact as end-user acceptance.

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
revert this mobile compile pass batch commit
```

Runtime rollback:

```text
none required; Lite remains default-off
```
