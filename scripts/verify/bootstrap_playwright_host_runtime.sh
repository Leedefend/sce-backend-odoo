#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
RUNTIME_ROOT="${PLAYWRIGHT_RUNTIME_ROOT:-${ROOT_DIR}/.codex-runtime/playwright-libs}"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "${TMP_DIR}"
}
trap cleanup EXIT

log() {
  printf '[bootstrap_playwright_host_runtime] %s\n' "$*"
}

require_bin() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf '[bootstrap_playwright_host_runtime] missing required binary: %s\n' "$1" >&2
    exit 1
  fi
}

download_libnss3_fallback() {
  require_bin curl
  require_bin rg
  local listing
  local deb_name
  listing="$(curl -fsSL "http://archive.ubuntu.com/ubuntu/pool/main/n/nss/")"
  deb_name="$(
    printf '%s' "${listing}" \
      | rg -o 'libnss3_[^" ]*22\.04\.[0-9]+_amd64\.deb' \
      | sort -u \
      | tail -n 1
  )"
  if [[ -z "${deb_name}" ]]; then
    printf '[bootstrap_playwright_host_runtime] unable to resolve libnss3 fallback package\n' >&2
    exit 1
  fi
  log "fallback download for libnss3 via ${deb_name}"
  curl -fsSLO "http://archive.ubuntu.com/ubuntu/pool/main/n/nss/${deb_name}"
}

download_package() {
  local package_name="$1"
  if apt download "${package_name}"; then
    return 0
  fi
  if [[ "${package_name}" == "libnss3" ]]; then
    download_libnss3_fallback
    return 0
  fi
  return 1
}

has_runtime_lib() {
  local lib_name="$1"
  local candidate
  for candidate in \
    "${RUNTIME_ROOT}/usr/lib/x86_64-linux-gnu/${lib_name}" \
    "${RUNTIME_ROOT}/lib/x86_64-linux-gnu/${lib_name}" \
    "${RUNTIME_ROOT}/usr/lib/${lib_name}" \
    "${RUNTIME_ROOT}/lib/${lib_name}"; do
    if [[ -f "${candidate}" ]]; then
      return 0
    fi
  done
  return 1
}

require_bin apt
require_bin dpkg-deb

mkdir -p "${RUNTIME_ROOT}"

required_libs=(
  libnspr4.so
  libnss3.so
  libnssutil3.so
  libatk-1.0.so.0
  libatk-bridge-2.0.so.0
  libatspi.so.0
  libXcomposite.so.1
  libXdamage.so.1
  libXfixes.so.3
  libXrandr.so.2
  libXi.so.6
  libXrender.so.1
  libgbm.so.1
  libwayland-server.so.0
  libxcb-randr.so.0
  libxkbcommon.so.0
  libasound.so.2
  libgtk-3.so.0
)

packages=(
  libnspr4
  libnss3
  libatk1.0-0
  libatk-bridge2.0-0
  libatspi2.0-0
  libxcomposite1
  libxdamage1
  libxfixes3
  libxrandr2
  libxi6
  libxrender1
  libgbm1
  libwayland-server0
  libxcb-randr0
  libxkbcommon0
  libasound2
  libgtk-3-0
)

missing_libs=()
for lib_name in "${required_libs[@]}"; do
  if ! has_runtime_lib "${lib_name}"; then
    missing_libs+=("${lib_name}")
  fi
done

if [[ "${#missing_libs[@]}" -eq 0 ]]; then
  log "runtime already ready at ${RUNTIME_ROOT}"
  exit 0
fi

log "bootstrap runtime at ${RUNTIME_ROOT}"
log "missing libs: ${missing_libs[*]}"

pushd "${TMP_DIR}" >/dev/null
for package_name in "${packages[@]}"; do
  download_package "${package_name}"
done
for deb_file in ./*.deb; do
  dpkg-deb -x "${deb_file}" "${RUNTIME_ROOT}"
done
popd >/dev/null

missing_after=()
for lib_name in "${required_libs[@]}"; do
  if ! has_runtime_lib "${lib_name}"; then
    missing_after+=("${lib_name}")
  fi
done

if [[ "${#missing_after[@]}" -gt 0 ]]; then
  printf '[bootstrap_playwright_host_runtime] runtime incomplete after bootstrap: %s\n' "${missing_after[*]}" >&2
  exit 1
fi

log "runtime ready at ${RUNTIME_ROOT}"
