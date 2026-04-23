#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"

PROFILE="${PROFILE:-}"
STEPS="${STEPS:-}"

if [[ -z "$PROFILE" && -z "$STEPS" ]]; then
  echo "ERROR: STEPS or PROFILE is required. e.g. STEPS=project_owner_demo_pm or PROFILE=demo_full" >&2
  exit 2
fi

ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"

if [[ -n "$PROFILE" ]]; then
  STEPS="profile:${PROFILE}"
fi

guard_seed_profile_prod
guard_seed_bootstrap_prod
guard_seed_db_explicit_prod

printf '[seed.run] db=%s steps=%s\n' "$DB_NAME" "$STEPS"

if [[ "${SEED_GUARD_ONLY:-}" == "1" ]]; then
  echo "[seed.run] guard-only mode; skip execution"
  exit 0
fi

compose_dev exec -T \
  -e STEPS="$STEPS" \
  -e SC_BOOTSTRAP_USERS \
  -e SC_BOOTSTRAP_ADMIN_LOGIN \
  -e SC_BOOTSTRAP_ADMIN_PASSWORD \
  -e SC_BOOTSTRAP_ADMIN_NAME \
  -e SC_BOOTSTRAP_ADMIN_GROUP_XMLIDS \
  -e SC_BOOTSTRAP_ADMIN_COMPANY_MODE \
  -e SC_BOOTSTRAP_UPDATE_PASSWORD \
  odoo odoo shell --config="$ODOO_CONF" -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
<<'PY'
from odoo.addons.smart_construction_seed.seed import run_steps
import os

steps = os.environ["STEPS"]
result = run_steps(env, steps)
print(result)
env.cr.commit()
PY
