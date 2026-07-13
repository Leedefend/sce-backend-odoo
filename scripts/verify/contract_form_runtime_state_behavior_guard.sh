#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$(mktemp -d)"
trap 'rm -rf "${OUT_DIR}"' EXIT

"${ROOT}/frontend/apps/web/node_modules/.bin/tsc" \
  --target ES2022 \
  --module commonjs \
  --moduleResolution node \
  --types node \
  --typeRoots "${ROOT}/frontend/apps/web/node_modules/@types" \
  --skipLibCheck \
  --rootDir "${ROOT}" \
  --outDir "${OUT_DIR}" \
  "${ROOT}/scripts/verify/contract_form_runtime_state_behavior_guard.ts" \
  "${ROOT}/frontend/apps/web/src/pages/contractForm/runtimeStateApplier.ts" \
  "${ROOT}/frontend/apps/web/src/pages/contractForm/runtimeStateReducer.ts" \
  "${ROOT}/frontend/apps/web/src/pages/contractForm/runtimeStateProtocol.ts"

echo '{"type":"commonjs"}' > "${OUT_DIR}/package.json"
node "${OUT_DIR}/scripts/verify/contract_form_runtime_state_behavior_guard.js"
