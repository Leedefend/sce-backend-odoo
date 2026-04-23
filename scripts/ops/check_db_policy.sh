#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB:-${1:-}}"

if [[ -z "$DB_NAME" ]]; then
  echo "FAIL DB not provided"
  echo "Allowed: sc_demo sc_p2 sc_p3"
  exit 2
fi

case "$DB_NAME" in
  sc_demo|sc_p2|sc_p3)
    exit 0
    ;;
  *)
    echo "DB not allowed by policy"
    echo "Allowed: sc_demo sc_p2 sc_p3"
    echo "To add exception: update docs/ops/codex_rules_v1.0.md + whitelist"
    exit 2
    ;;
esac
