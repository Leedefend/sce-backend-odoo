# Unified Semantic Page Contract Lite - Mobile Environment Readiness

Date: 2026-05-03
Branch: `codex/mobile-contract-sync-plan`

## Status

The mobile branch has been rebased onto `origin/main` and the repository-level
mobile contract gates are executable.

Current decision:

```text
mobile_code_ready_terminal_device_environment_pending
```

## Verified Locally

Executed after installing frontend workspace dependencies with the frozen
lockfile:

```bash
CI=true pnpm install --frozen-lockfile
python3 -m py_compile $(git diff --name-only origin/main...HEAD -- 'scripts/verify/*.py')
make verify.unified_page_contract.lite.terminal_coverage_matrix
make verify.unified_page_contract.lite.wx_mini_compile_pilot.host
make verify.unified_page_contract.lite.wx_mini_real_compile_pilot.host
make verify.unified_page_contract.lite.wx_mini_runtime_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_compile_pilot.host
make verify.unified_page_contract.lite.harmony_h5_runtime_acceptance_pilot.host
```

Observed decisions:

```text
terminal_matrix_device_probes_ready_runners_pending
wx_mini_compile_pilot_ready
wx_mini_real_compile_pilot_passed
wx_mini_runtime_artifact_acceptance_pilot_passed
harmony_h5_compile_pilot_passed
harmony_h5_runtime_browser_acceptance_pilot_passed
```

Generated build output under `frontend/apps/mobile/dist/` is a local verification
artifact and must not be committed.

## Environment Blockers

The final device acceptance probes are implemented and runnable, but this
machine does not expose the required terminal runners.

Missing WeChat mini-program runner:

```text
wechat-devtools
wechatwebdevtools
wxdt
cli
```

Missing Harmony runner:

```text
hdc
deveco
deveco-studio
HARMONY_HDC / HARMONY_DEVTOOLS_CLI / DEVECO_CLI
```

Current device-gate decisions:

```text
wx_mini_device_acceptance_pilot_blocked_missing_wechat_devtools_cli
harmony_h5_device_acceptance_pilot_blocked_missing_harmony_runner
```

These are environment blockers, not code failures.

## Next Gate

After the terminal runners are available, rerun:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
```

Only after those runners prove the terminal/device path should this branch be
treated as fully accepted for mobile delivery.
