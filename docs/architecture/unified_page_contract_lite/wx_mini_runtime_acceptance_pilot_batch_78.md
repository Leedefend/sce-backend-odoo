# Unified Semantic Page Contract Lite - wx_mini Runtime Artifact Acceptance Batch 78

Date: 2026-05-03
Status: compiled artifact acceptance passed

## 1. Boundary

Layer Target: Frontend Mobile Runtime Artifact Acceptance

Module:

- `frontend/apps/mobile`
- `scripts/verify`
- `docs/architecture/unified_page_contract_lite`
- `Makefile`

Reason:

The wx_mini real compile gate proves the mini-program can be built. It does not
prove the generated artifact contains an importable app entry and the expected
contract page. This batch adds a narrow artifact acceptance gate before any
WeChat developer tool or device acceptance gate.

## 2. Guarded Target

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
```

The target executes a real compile and then checks:

- `dist/build/mp-weixin/app.json`
- `dist/build/mp-weixin/project.config.json`
- `dist/build/mp-weixin/app.js`
- `dist/build/mp-weixin/app.wxss`
- `dist/build/mp-weixin/App.wxml`
- `dist/build/mp-weixin/common/vendor.js`
- `dist/build/mp-weixin/pages/contract/index.js`
- `dist/build/mp-weixin/pages/contract/index.json`
- `dist/build/mp-weixin/pages/contract/index.wxml`
- `dist/build/mp-weixin/pages/contract/index.wxss`

It also verifies that `app.json` registers:

```text
pages/contract/index
```

## 3. Current Decision

```text
wx_mini_runtime_artifact_acceptance_pilot_passed
```

This means the generated mini-program artifact has the expected entry shape. It
does not mean the artifact has been accepted in WeChat developer tools or on a
device.

## 4. Non-Goals

This batch does not:

- run WeChat developer tools
- run a device acceptance test
- connect the mini-program runtime to a live backend
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Next Gate

Next executable gate:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
```

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite
```

## 7. Rollback

Code rollback:

```text
revert this runtime artifact acceptance batch commit
```

Runtime rollback:

```text
none required; Lite remains default-off
```
