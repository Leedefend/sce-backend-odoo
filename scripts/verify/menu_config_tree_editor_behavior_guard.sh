#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT_DIR="$(mktemp -d)"
trap 'rm -rf "${OUT_DIR}"' EXIT

"${ROOT}/scripts/dev/pnpm_exec.sh" -C "${ROOT}/frontend/apps/web" exec esbuild \
  "${ROOT}/scripts/verify/menu_config_tree_editor_behavior_guard.ts" \
  --bundle \
  --platform=node \
  --format=esm \
  --outfile="${OUT_DIR}/menu_config_tree_editor_behavior_guard.mjs"

node "${OUT_DIR}/menu_config_tree_editor_behavior_guard.mjs"
