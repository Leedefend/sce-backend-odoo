# Unified Semantic Page Contract Lite - Terminal Coverage Matrix Runtime Mount Batch 71

Date: 2026-05-03
Status: implemented guard update

## 1. Boundary

Layer Target: Contract Verification / All-Terminal Coverage

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`

Reason:

After wx_mini and harmony_h5 runtime mount pilot gates were added, the coverage
matrix must report the current state: runtime mount is ready, but real terminal
compilation is still pending.

## 2. Updated Decision

```text
terminal_matrix_runtime_mount_ready_compile_pending
```

This means:

- `web_pc` remains the covered browser acceptance anchor
- `wx_mini` has semantic parity, renderer input readiness, UI renderer readiness,
  page integration readiness, and runtime mount readiness
- `harmony_h5` has semantic parity, renderer input readiness, UI renderer
  readiness, page integration readiness, and runtime mount readiness
- neither mobile terminal is fully covered until compile/smoke passes

## 3. Non-Goals

This batch does not:

- implement UniApp pages
- implement Harmony H5 pages
- compile terminal apps
- start terminal runtimes
- dispatch user actions
- change backend contract shape
- add terminal-specific contract fields

## 4. Next Required Gates

The next terminal implementation gates are:

```bash
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
make verify.unified_page_contract.lite.harmony_h5_compile_pilot.host
```

These gates must prove terminal compilation and smoke readiness, not just runtime
mount shape.

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
