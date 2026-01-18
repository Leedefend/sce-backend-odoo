#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
guard_prod_forbid

make audit.project.actions DB=sc_demo
python3 scripts/ci/assert_audit_tp08.py
