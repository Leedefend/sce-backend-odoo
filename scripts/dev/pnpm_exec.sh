#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

if [[ -n "${PNPM_BIN:-}" ]]; then
  exec "${PNPM_BIN}" "$@"
fi

PNPM_VERSION="$(
  ROOT_DIR="${ROOT_DIR}" node - <<'NODE'
const pkg = require(`${process.env.ROOT_DIR}/frontend/package.json`);
const spec = String(pkg.packageManager || 'pnpm@').trim();
const match = spec.match(/^pnpm@(.+)$/);
if (!match) {
  process.exit(2);
}
process.stdout.write(match[1]);
NODE
)"

candidate_paths=()
if [[ -n "${COREPACK_HOME:-}" ]]; then
  candidate_paths+=("${COREPACK_HOME}/v1/pnpm/${PNPM_VERSION}/bin/pnpm.cjs")
fi
candidate_paths+=(
  "${ROOT_DIR}/../.corepack/v1/pnpm/${PNPM_VERSION}/bin/pnpm.cjs"
  "${HOME}/.cache/node/corepack/v1/pnpm/${PNPM_VERSION}/bin/pnpm.cjs"
  "${HOME}/.local/share/node/corepack/v1/pnpm/${PNPM_VERSION}/bin/pnpm.cjs"
)

for candidate in "${candidate_paths[@]}"; do
  if [[ -f "${candidate}" ]]; then
    exec node "${candidate}" "$@"
  fi
done

if command -v pnpm >/dev/null 2>&1; then
  current_version="$(pnpm --version 2>/dev/null || true)"
  if [[ "${current_version}" == "${PNPM_VERSION}" ]]; then
    exec pnpm "$@"
  fi
fi

if command -v corepack >/dev/null 2>&1; then
  export COREPACK_ENABLE_DOWNLOAD_PROMPT=0
  exec corepack pnpm "$@"
fi

echo "pnpm ${PNPM_VERSION} is required but was not found" >&2
exit 2
