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
parity, renderer input pilot gates, UI renderer pilot gates, page integration
pilot gates, runtime mount pilot gates, and real compile gates. wx_mini has
compiled runtime artifact acceptance and a device acceptance probe. harmony_h5
has browser runtime acceptance and a device acceptance probe. Actual device
runners are still pending.

## 2. Current Matrix

| Client | Contract parity | Renderer input pilot | UI renderer pilot | Page integration pilot | Runtime mount pilot | Compile preflight | Acceptance status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `web_pc` | pass | available | available | available | available | available | covered browser anchor |
| `wx_mini` | pass | available | available | available | available | available | device-acceptance-probe-ready, device-runner-pending |
| `harmony_h5` | pass | available | available | available | available | available | device-acceptance-probe-ready, device-runner-pending |

`web_pc` is the current browser acceptance anchor.

`wx_mini` has a device acceptance probe but device runner is pending.

`harmony_h5` has a device acceptance probe but device runner is pending.

They must not be reported as fully covered until their guarded compile pilot
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
- mini program and Harmony H5 UI renderer pilot gates remain present
- mini program and Harmony H5 page integration pilot gates remain present
- mini program and Harmony H5 runtime mount pilot gates remain present
- mini program compile preflight gate remains present
- mini program real compile pilot gate remains present
- mini program runtime artifact acceptance pilot gate remains present
- mini program device acceptance pilot gate remains present
- mini program is explicitly marked device-runner-pending
- Harmony H5 compile pilot gate remains present
- Harmony H5 runtime acceptance pilot gate remains present
- Harmony H5 device acceptance pilot gate remains present
- Harmony H5 is explicitly marked device-runner-pending
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
make verify.unified_page_contract.lite.wx_mini_page_integration_pilot.host
make verify.unified_page_contract.lite.harmony_h5_page_integration_pilot.host
make verify.unified_page_contract.lite.wx_mini_runtime_mount_pilot.host
make verify.unified_page_contract.lite.harmony_h5_runtime_mount_pilot.host
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
make verify.unified_page_contract.lite.wx_mini_device_runner_acceptance.host
make verify.unified_page_contract.lite.harmony_h5_compile_pilot.host
make verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_device_runner_acceptance.host
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
