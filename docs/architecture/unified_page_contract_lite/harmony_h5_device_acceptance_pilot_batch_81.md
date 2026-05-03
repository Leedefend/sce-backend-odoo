# Unified Semantic Page Contract Lite - harmony_h5 Device Acceptance Probe Batch 81

Date: 2026-05-03
Status: probe implemented, device runner pending

## 1. Boundary

Layer Target: Frontend Mobile Device Acceptance Governance

Module:

- `frontend/apps/mobile`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

The harmony_h5 browser runtime acceptance gate proves the compiled H5 artifact
loads in headless Chromium. It does not prove a Harmony container or device
runner is available. This batch adds an explicit runner probe so missing DevEco
or `hdc` tooling remains visible.

## 2. Guarded Target

Run:

```bash
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
```

The target depends on:

```bash
make verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host
```

Then it checks:

- `dist/build/h5/index.html`
- compiled H5 index JavaScript asset
- compiled H5 contract page JavaScript asset
- app mount node in `index.html`
- Harmony device runner availability

Supported runner discovery:

- `HARMONY_HDC`
- `HARMONY_DEVTOOLS_CLI`
- `DEVECO_CLI`
- `hdc`
- `deveco`
- `deveco-studio`

## 3. Current Decision

```text
harmony_h5_device_acceptance_pilot_blocked_missing_harmony_runner
```

This means the compiled H5 artifact remains valid, but the current environment
does not expose a Harmony runner. This is not a code failure and must not be
reported as device acceptance passed.

## 4. Non-Goals

This batch does not:

- run a Harmony device or container
- run DevEco Studio
- connect the H5 runtime to a live backend
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Next Gate

Next executable gate after a runner exists:

```bash
make verify.unified_page_contract.lite.harmony_h5_device_runner_acceptance.host
```

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this device acceptance probe batch commit
```

Runtime rollback:

```text
none required; Lite remains default-off
```
