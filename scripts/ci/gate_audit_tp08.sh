#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
guard_prod_forbid
LOG_DIR="$ROOT_DIR/artifacts/logs"
mkdir -p "$LOG_DIR"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${TS}_tp08_gate.log"

{
  make audit.project.actions DB=sc_demo
  python3 scripts/ci/assert_audit_tp08.py
} 2>&1 | tee "$LOG_FILE"
