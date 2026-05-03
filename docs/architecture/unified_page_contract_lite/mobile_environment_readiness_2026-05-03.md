# Unified Semantic Page Contract Lite - Mobile Environment Readiness

Date: 2026-05-03
Branch: `codex/mobile-contract-sync-plan`

## Status

The mobile branch has been rebased onto `origin/main` and the repository-level
mobile contract gates are executable.

Current decision:

```text
mobile_code_ready_device_runners_ready_manual_device_pending
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

The Harmony runner is available through WSL wrappers after installing DevEco
Studio from Windows:

```text
~/.local/bin/hdc -> D:\Program Files\Huawei\DevEco Studio\sdk\default\openharmony\toolchains\hdc.exe
~/.local/bin/deveco-studio -> D:\Program Files\Huawei\DevEco Studio\bin\devecostudio64.exe
```

Runner probe:

```text
hdc -v
Ver: 3.2.0d
```

Current harmony_h5 decision:

```text
harmony_h5_device_acceptance_runner_ready_manual_device_pending
```

Both terminal runners are now available. The remaining gate is manual/physical
device confirmation, not repository code or local runner setup.

## WSL Helper

Use this helper after installing Windows-side tooling:

```bash
bash scripts/ops/setup_mobile_device_acceptance_wsl.sh
```

It creates WSL wrappers under `~/.local/bin` for:

```text
wechat-devtools
hdc
deveco-studio
```

The wrappers allow the existing Makefile device probes to discover Windows-side
tools from WSL.

## Next Gate

Before manual device confirmation, rerun:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
```

Both should report `*_runner_ready_manual_device_pending`. Treat that as runner
readiness, not as final end-user device acceptance.
