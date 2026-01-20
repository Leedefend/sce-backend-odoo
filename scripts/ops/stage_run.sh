#!/usr/bin/env bash
set -euo pipefail

STAGE_NAME="${STAGE:-${1:-}}"
DB_NAME="${DB:-${2:-}}"

trap 'echo "STAGE_RESULT: FAIL"' ERR

if [[ -z "$STAGE_NAME" ]]; then
  echo "FAIL: STAGE is required"
  exit 2
fi

if [[ -z "$DB_NAME" ]]; then
  echo "FAIL: DB is required"
  exit 2
fi

DB="$DB_NAME" bash scripts/ops/stage_preflight.sh

make ci.gate.tp08 DB=sc_demo

case "$STAGE_NAME" in
  p2*)
    make p2.smoke DB="$DB_NAME"
    ;;
  p3*)
    make p3.smoke DB="$DB_NAME"
    make p3.audit DB="$DB_NAME"
    ;;
  *)
    echo "FAIL: unsupported STAGE '${STAGE_NAME}'"
    exit 2
    ;;
esac

echo "STAGE_RESULT: PASS"
