#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# Fail closed before loading defaults or invoking module/database operations.
source "$ROOT_DIR/scripts/common/frontend_acceptance_guard.sh"
guard_frontend_acceptance_scope
acquire_frontend_acceptance_lock lifecycle

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"

guard_prod_forbid
export DB_NAME SC_ENVIRONMENT SC_ALLOW_DEMO_DATA

make --no-print-directory policy.ensure.role_surface_demo \
  DB_NAME="$DB_NAME" AUTO_FIX_ROLE_SURFACE_DEMO=1 ROLE_SMOKE_PASSWORD=demo

DB_NAME="$DB_NAME" make --no-print-directory odoo.shell.exec <<'PY'
import json
from odoo.addons.smart_construction_demo.tools.frontend_productization_fixture import ensure_fixture

summary = ensure_fixture(env)
env.cr.commit()
print("[demo.frontend.fixture] PASS")
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
