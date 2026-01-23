#!/usr/bin/env bash
set -euo pipefail

pattern="contains\\(\\.[[:space:]]*,[[:space:]]*['\\\"]"
hits=$(rg -n --glob '*.xml' -e "$pattern" addons/smart_construction_core/views || true)

if [[ -n "$hits" ]]; then
  echo "[AUTH_XPATH_GUARD][FAIL] Avoid text-based contains() in auth views."
  echo "$hits"
  exit 1
fi

echo "[AUTH_XPATH_GUARD][PASS]"
