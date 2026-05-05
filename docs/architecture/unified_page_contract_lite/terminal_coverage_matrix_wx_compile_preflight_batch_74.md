# Unified Semantic Page Contract Lite - Terminal Coverage Matrix wx_mini Compile Preflight Batch 74

Date: 2026-05-03
Status: implemented guard update

## 1. Boundary

Layer Target: Contract Verification / All-Terminal Coverage

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`

Reason:

After the wx_mini mobile workspace skeleton was added, the coverage matrix must
distinguish compile preflight readiness from real mini-program compilation.

## 2. Updated Decision

```text
terminal_matrix_wx_compile_preflight_ready_harmony_compile_pending
```

This means:

- `web_pc` remains the covered browser acceptance anchor
- `wx_mini` has compile preflight readiness
- `wx_mini` has not completed real mini-program compilation
- `harmony_h5` remains runtime-mount-ready and compile-pending

## 3. Non-Goals

This batch does not:

- install UniApp dependencies
- run real mini-program compilation
- run H5 compilation
- start terminal runtimes
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields

## 4. Next Required Gates

The next terminal implementation gates are:

```bash
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
make verify.unified_page_contract.lite.harmony_h5_compile_pilot.host
```

## 5. Verification

Run:

```bash
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite
```

## 6. Rollback

Code rollback:

```text
revert this guard update batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
