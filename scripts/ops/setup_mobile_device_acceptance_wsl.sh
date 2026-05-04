#!/usr/bin/env bash
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
mkdir -p "${BIN_DIR}"

write_wrapper() {
  local name="$1"
  local windows_path="$2"
  local target="${BIN_DIR}/${name}"

  cat > "${target}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
TOOL="${windows_path}"
if [[ ! -f "\${TOOL}" ]]; then
  echo "${name} target not found: \${TOOL}" >&2
  exit 127
fi
cd /mnt/c/Windows
exec cmd.exe /C "\$(wslpath -w "\${TOOL}")" "\$@"
EOF
  chmod +x "${target}"
  echo "${name}: ${target} -> ${windows_path}"
}

write_probe_wrapper() {
  local name="$1"
  local windows_path="$2"
  local target="${BIN_DIR}/${name}"

  cat > "${target}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
TOOL="${windows_path}"
if [[ ! -f "\${TOOL}" ]]; then
  echo "${name} target not found: \${TOOL}" >&2
  exit 127
fi
if [[ "\${1:-}" == "version" || "\${1:-}" == "--version" || "\${1:-}" == "-v" ]]; then
  echo "${name} wrapper: \${TOOL}"
  exit 0
fi
cd /mnt/c/Windows
exec cmd.exe /C "\$(wslpath -w "\${TOOL}")" "\$@"
EOF
  chmod +x "${target}"
  echo "${name}: ${target} -> ${windows_path}"
}

find_first() {
  local pattern="$1"
  shift
  find "$@" -maxdepth 8 -iname "${pattern}" 2>/dev/null | head -1
}

WECHAT_CLI=""
if [[ -f "/mnt/c/Program Files (x86)/Tencent/微信web开发者工具/cli.bat" ]]; then
  WECHAT_CLI="/mnt/c/Program Files (x86)/Tencent/微信web开发者工具/cli.bat"
elif [[ -f "/mnt/c/Program Files/Tencent/微信web开发者工具/cli.bat" ]]; then
  WECHAT_CLI="/mnt/c/Program Files/Tencent/微信web开发者工具/cli.bat"
else
  WECHAT_CLI="$(find_first "cli.bat" "/mnt/c/Program Files" "/mnt/c/Program Files (x86)" "/mnt/c/Users" || true)"
fi

if [[ -n "${WECHAT_CLI}" ]]; then
  write_wrapper "wechat-devtools" "${WECHAT_CLI}"
else
  echo "wechat-devtools: Windows WeChat DevTools CLI not found" >&2
fi

HDC_EXE=""
for candidate in \
  "/mnt/d/Program Files/Huawei/DevEco Studio/sdk/default/openharmony/toolchains/hdc.exe" \
  "/mnt/d/Program Files/Huawei/DevEco Studio/sdk/HarmonyOS-NEXT-DB1/openharmony/toolchains/hdc.exe" \
  "/mnt/d/Program Files/Huawei/DevEco Studio/tools/hdc.exe"; do
  if [[ -f "${candidate}" ]]; then
    HDC_EXE="${candidate}"
    break
  fi
done
if [[ -z "${HDC_EXE}" ]]; then
  HDC_EXE="$(find_first "hdc.exe" "/mnt/c/Users/12472/AppData/Local/Huawei" "/mnt/d/Program Files/Huawei" "/mnt/e/huawei" "/mnt/e/huawei2" || true)"
fi
if [[ -n "${HDC_EXE}" ]]; then
  write_wrapper "hdc" "${HDC_EXE}"
else
  echo "hdc: Windows hdc.exe not found" >&2
fi

DEVECO_EXE=""
for candidate in \
  "/mnt/d/Program Files/Huawei/DevEco Studio/bin/devecostudio64.exe" \
  "/mnt/d/Program Files/Huawei/DevEco Studio/bin/devecostudio.bat"; do
  if [[ -f "${candidate}" ]]; then
    DEVECO_EXE="${candidate}"
    break
  fi
done
if [[ -z "${DEVECO_EXE}" ]]; then
  DEVECO_EXE="$(find_first "deveco*.exe" "/mnt/d/Program Files/Huawei" "/mnt/c/Users/12472/AppData/Local/Huawei" "/mnt/e/huawei" "/mnt/e/huawei2" || true)"
fi
if [[ -n "${DEVECO_EXE}" ]]; then
  write_probe_wrapper "deveco-studio" "${DEVECO_EXE}"
else
  echo "deveco-studio: Windows DevEco Studio not found" >&2
fi
