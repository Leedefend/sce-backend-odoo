#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

echo "[check] repo: $(pwd)"

if [[ -f .gitmodules ]]; then
  echo "[check] .gitmodules present"
else
  echo "[warn] .gitmodules missing"
fi

if [[ -d addons_external/oca_server_ux/base_tier_validation ]]; then
  echo "[OK] base_tier_validation present"
else
  echo "[FAIL] base_tier_validation missing: addons_external/oca_server_ux/base_tier_validation"
  echo "Fix:"
  echo "  git submodule sync --recursive && git submodule update --init --recursive"
  exit 2
fi
