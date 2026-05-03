# Unified Semantic Page Contract Lite - Mobile Environment Readiness

Date: 2026-05-03
Branch: `codex/mobile-contract-sync-plan`

## Status

The mobile branch has been rebased onto `origin/main` and the repository-level
mobile contract gates are executable.

Current decision:

```text
mobile_code_ready_wx_runner_ready_harmony_runner_pending
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

## Device Runner Status

The final device acceptance probes are implemented and runnable.

The WeChat mini-program runner is available through a WSL wrapper:

```text
~/.local/bin/wechat-devtools -> C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat
```

Current wx_mini decision:

```text
wx_mini_device_acceptance_runner_ready_manual_device_pending
```

The Harmony runner is still missing. A non-interactive WinGet attempt for
`Huawei.DevEcoDeviceTool` downloaded the installer but did not complete package
registration in this WSL-driven session. Complete DevEco Device Tool / DevEco
Studio installation from the Windows GUI, then rerun the WSL setup helper.

Missing Harmony runner commands:

```text
hdc
deveco
deveco-studio
HARMONY_HDC / HARMONY_DEVTOOLS_CLI / DEVECO_CLI
```

Current harmony_h5 decision:

```text
harmony_h5_device_acceptance_pilot_blocked_missing_harmony_runner
```

The Harmony blocker is an environment blocker, not a code failure.

## WSL Helper

Use this helper after installing Windows-side tooling:

```bash
bash scripts/ops/setup_mobile_device_acceptance_wsl.sh
```

It creates WSL wrappers under `~/.local/bin` for:

```text
wechat-devtools
hdc
deveco
```

The wrappers allow the existing Makefile device probes to discover Windows-side
tools from WSL.

## Next Gate

After the Harmony runner is available, rerun:

```bash
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
```

The WeChat runner probe is already ready, but still requires manual/device-level
confirmation before it should be treated as end-user device acceptance.
