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

HDC_EXE="$(find_first "hdc.exe" "/mnt/c/Program Files" "/mnt/c/Program Files (x86)" "/mnt/c/Users" "/mnt/c/tools" || true)"
if [[ -n "${HDC_EXE}" ]]; then
  write_wrapper "hdc" "${HDC_EXE}"
else
  echo "hdc: Windows hdc.exe not found" >&2
fi

DEVECO_EXE="$(find_first "deveco*.exe" "/mnt/c/Program Files" "/mnt/c/Program Files (x86)" "/mnt/c/Users" "/mnt/c/tools" || true)"
if [[ -n "${DEVECO_EXE}" ]]; then
  write_wrapper "deveco" "${DEVECO_EXE}"
else
  echo "deveco: Windows DevEco CLI not found" >&2
fi
