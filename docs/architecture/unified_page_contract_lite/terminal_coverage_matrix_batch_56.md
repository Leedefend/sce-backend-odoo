# Unified Semantic Page Contract Lite - Terminal Coverage Matrix Batch 56

Date: 2026-05-03
Status: implemented guard

## 1. Boundary

Layer Target: Contract Verification / All-Terminal Coverage

Module:

- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

All-terminal coverage needs a truthful matrix. Web PC already has browser
acceptance gates. UniApp mini program and Harmony H5 have semantic contract
parity and renderer input pilot gates, but no UI renderer pilot yet. The matrix
must make that gap visible before implementation begins.

## 2. Current Matrix

| Client | Contract parity | Renderer input pilot | UI renderer pilot | Acceptance status |
| --- | --- | --- | --- | --- |
| `web_pc` | pass | available | available | covered browser anchor |
| `wx_mini` | pass | available | pending | renderer-input-ready, UI-renderer-pending |
| `harmony_h5` | pass | available | pending | renderer-input-ready, UI-renderer-pending |

`web_pc` is the current browser acceptance anchor.

`wx_mini` and `harmony_h5` are renderer-input-ready but UI-renderer-pending.

They must not be reported as fully covered until their guarded UI renderer pilot
gates exist and pass.

## 3. Guard

This batch adds:

```bash
make verify.unified_page_contract.lite.terminal_coverage_matrix
```

The guard reads:

- `artifacts/backend/unified_page_contract_lite_terminal_client_parity.json`
- `all_terminal_coverage_plan_batch_54.md`
- `terminal_client_parity_batch_55.md`
- this matrix document
- `Makefile`

It verifies:

- `web_pc`, `wx_mini`, and `harmony_h5` share contract parity
- Web all-tree acceptance gates remain present
- mini program and Harmony H5 renderer input pilot gates remain present
- mini program and Harmony H5 are explicitly marked UI-renderer-pending
- future pilot gates are named as next required gates

## 4. Non-Goals

This matrix does not:

- implement the mini program renderer
- implement the Harmony H5 renderer
- add terminal-specific contract fields
- change Lite schema
- change backend runtime behavior
- enable Lite by default

## 5. Next Required Gates

The next implementation batches must add and pass:

```bash
make verify.unified_page_contract.lite.wx_mini_ui_renderer_pilot.host
make verify.unified_page_contract.lite.harmony_h5_ui_renderer_pilot.host
```

Those gates must prove terminal rendering and interaction, not just contract
shape.

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this guard batch commit
```

Runtime rollback:

```text
none required; this batch has no runtime path
```
