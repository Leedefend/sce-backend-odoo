#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
cd "$ROOT_DIR"

echo "[verify.test_seed_dependency.guard] scanning tests for external seed/demo dependencies..."

patterns=(
  "Run seed step"
  "Missing demo"
  "requires demo seed"
  "need demo seed"
)

scan_dirs=(
  "addons/smart_core/tests"
  "addons/smart_construction_core/tests"
)

hits=""
for p in "${patterns[@]}"; do
  found="$(rg -n -i --glob '*.py' --glob '*.pyc' -g'!**/__pycache__/**' "$p" "${scan_dirs[@]}" || true)"
  if [ -n "$found" ]; then
    hits+=$'\n'"# pattern: $p"$'\n'"$found"$'\n'
  fi
done

if [ -n "$hits" ]; then
  echo "[verify.test_seed_dependency.guard] FAIL: detected test code that depends on external demo/seed state."
  echo "$hits"
  echo "[verify.test_seed_dependency.guard] HINT: tests must create their own fixtures in setUpClass/setUp."
  exit 2
fi

echo "[verify.test_seed_dependency.guard] PASS"
