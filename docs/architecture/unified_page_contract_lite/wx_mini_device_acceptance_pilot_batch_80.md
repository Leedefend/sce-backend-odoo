# Unified Semantic Page Contract Lite - wx_mini Device Acceptance Probe Batch 80

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

The wx_mini compiled artifact acceptance gate proves the mini-program output is
importable in shape. It does not prove WeChat developer tools or a device runner
is available. This batch adds an explicit device acceptance probe so the matrix
does not silently treat the missing runner as covered.

## 2. Guarded Target

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
```

The target depends on:

```bash
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
```

Then it checks:

- `dist/build/mp-weixin/app.json`
- `dist/build/mp-weixin/project.config.json`
- `dist/build/mp-weixin/app.js`
- `dist/build/mp-weixin/pages/contract/index.wxml`
- `app.json` registers `pages/contract/index`
- WeChat developer tools CLI availability

Supported CLI discovery:

- `WECHAT_DEVTOOLS_CLI`
- `WX_DEVTOOLS_CLI`
- `wechat-devtools`
- `wechatwebdevtools`
- `wxdt`
- `cli`

## 3. Current Decision

```text
wx_mini_device_acceptance_pilot_blocked_missing_wechat_devtools_cli
```

This means the compiled artifact remains valid, but the current environment
does not expose a WeChat developer tools CLI or device runner. This is not a
code failure and must not be reported as device acceptance passed.

## 4. Non-Goals

This batch does not:

- run WeChat developer tools
- run a real device acceptance test
- connect the mini-program runtime to a live backend
- change backend contract shape
- add terminal-specific contract fields
- enable Lite by default

## 5. Next Gate

Next executable gate after a runner exists:

```bash
make verify.unified_page_contract.lite.wx_mini_device_runner_acceptance.host
```

## 6. Verification

Run:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
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
