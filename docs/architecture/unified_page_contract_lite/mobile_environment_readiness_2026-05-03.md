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

The wrapper starts `cmd.exe` from `C:\Windows` so the Windows CLI does not use
the WSL UNC repository path as its current directory.

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

Additional runner probes:

```text
wechat-devtools --project <compiled mp-weixin path> --disable-gpu --version
```

This command starts the Windows WeChat developer tool process and returns CLI
help with exit code 0. Windows process evidence showed `WeChatAppEx` running
after the probe.

```text
hdc list targets
[Empty]
```

This proves the Harmony `hdc` runner is callable, but no Harmony device or
container is connected in the current environment.

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

For WeChat DevTools, the first CLI call can still require one Windows-side
setting:

```text
WeChat DevTools -> Settings -> Security Settings -> Service Port -> On
```

If the CLI reports `IDE service port disabled` or `wait IDE port timeout`, open
the WeChat DevTools GUI once, enable the service port manually, then rerun:

```bash
pnpm -C frontend/apps/mobile build:mp-weixin
wechat-devtools open --project "$(wslpath -w "$PWD/frontend/apps/mobile/dist/build/mp-weixin")" --disable-gpu
```

In this WSL environment, WeChat DevTools is more stable when the generated
mini-program project is copied to a Windows-local directory before import:

```bash
pnpm -C frontend/apps/mobile build:mp-weixin:windows
```

Default Windows-local project directory:

```text
C:\Users\12472\sce-mobile-mp-weixin
```

Override the sync destination with `SC_MOBILE_WX_WINDOWS_DIR` when another
Windows user profile or drive is used.

For Harmony H5, build and copy the generated H5 runtime to a Windows-local
directory with:

```bash
pnpm -C frontend/apps/mobile build:h5:harmony:windows
```

Default Windows-local Harmony H5 directory:

```text
C:\Users\12472\sce-mobile-harmony-h5
```

Override the sync destination with `SC_MOBILE_HARMONY_WINDOWS_DIR` when another
Windows user profile or drive is used.

Serve the Harmony H5 build for a physical device or DevEco browser container
with:

```bash
pnpm -C frontend/apps/mobile serve:h5:harmony
```

Default local URL:

```text
http://127.0.0.1:8091
```

Use the printed LAN URL on a physical Harmony device. Override the server port
with `SC_MOBILE_HARMONY_PORT` when needed.

WSL localhost forwarding is enough for Windows-local browser checks, but it may
not expose the H5 server or backend service to a physical Harmony device on the
same LAN. Without administrator `netsh portproxy`, start the Windows-local
gateway from PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File \\wsl.localhost\Ubuntu\home\odoo\workspace\sce-backend-odoo\scripts\ops\start_mobile_harmony_h5_windows_gateway.ps1
```

The gateway serves the synced H5 bundle on port `8092` and proxies the backend
to port `8071`. On the Harmony device, open:

```text
http://<computer-lan-ip>:8092
```

Then set the login page service URL to:

```text
http://<computer-lan-ip>:8071
```

DevEco Studio cannot directly open the H5 output directory because
`C:\Users\12472\sce-mobile-harmony-h5` is only a static web bundle. Prepare the
DevEco importable Harmony shell project with:

```bash
pnpm -C frontend/apps/mobile prepare:harmony:windows
```

Open this Windows-local project directory in DevEco Studio:

```text
C:\Users\12472\sce-mobile-harmony-shell
```

The shell is a minimal ArkTS Stage project with a WebView that loads the H5
gateway URL. Command-line builds require DevEco's bundled Node, SDK, and JBR in
the current PowerShell session:

```powershell
$env:NODE_HOME="D:\Program Files\Huawei\DevEco Studio\tools\node"
$env:DEVECO_SDK_HOME="D:\Program Files\Huawei\DevEco Studio\sdk"
$env:JAVA_HOME="D:\Program Files\Huawei\DevEco Studio\jbr"
$env:PATH="$env:JAVA_HOME\bin;$env:NODE_HOME;$env:PATH"
cd C:\Users\12472\sce-mobile-harmony-shell
& "D:\Program Files\Huawei\DevEco Studio\tools\hvigor\bin\hvigorw.bat" assembleHap --no-daemon
```

Current command-line HAP output:

```text
C:\Users\12472\sce-mobile-harmony-shell\entry\build\default\outputs\default\entry-default-unsigned.hap
```

The current mobile first page is:

```text
pages/login/index
```

The login page collects service URL, database, account, and password, then calls
the unified `/api/v1/intent` `login` intent. For physical phone testing, the
service URL must be the computer LAN address, not `127.0.0.1`.

Current local simulated production service:

```text
http://127.0.0.1:8070
db=sc_prod_sim
```

After login, the mobile runtime opens:

```text
pages/home/index
```

The page displays session facts from the login response and exposes the current
contract runtime page as a secondary entry.

## Next Gate

Before manual device confirmation, rerun:

```bash
make verify.unified_page_contract.lite.wx_mini_device_acceptance_pilot.host
make verify.unified_page_contract.lite.harmony_h5_device_acceptance_pilot.host
```

Both should report `*_runner_ready_manual_device_pending`. Treat that as runner
readiness, not as final end-user device acceptance.

Manual confirmation checklist:

```text
wx_mini: open the generated mp-weixin project in WeChat DevTools and verify the contract page renders.
harmony_h5: connect a Harmony device/container so hdc list targets is non-empty, then open the generated H5 runtime.
```
