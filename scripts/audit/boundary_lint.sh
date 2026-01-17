#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAIL=0

check_manifest() {
  local file="$1"
  local pattern="$2"
  if rg -n "$pattern" "$ROOT_DIR/$file" >/dev/null 2>&1; then
    echo "FAIL: $file contains forbidden pattern: $pattern"
    rg -n "$pattern" "$ROOT_DIR/$file" || true
    FAIL=1
  fi
}

CORE_MANIFEST="addons/smart_construction_core/__manifest__.py"
CUSTOM_MANIFEST="addons/smart_construction_custom/__manifest__.py"
SEED_MANIFEST="addons/smart_construction_seed/__manifest__.py"

check_manifest "$CORE_MANIFEST" "dictionary_demo\\.xml"
check_manifest "$CORE_MANIFEST" "cost_demo\\.xml"
check_manifest "$CORE_MANIFEST" "project_demo_banner_views\\.xml"
check_manifest "$CORE_MANIFEST" "demo/sc_demo_users\\.xml"

check_manifest "$CUSTOM_MANIFEST" "role_matrix_demo_users\\.xml"

check_manifest "$SEED_MANIFEST" "sc_demo_showcase_actions\\.xml"

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi

echo "OK: boundary lint passed."
