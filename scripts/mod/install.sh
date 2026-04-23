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

: "${MODULE:?MODULE is required. e.g. MODULE=smart_construction_core}"
: "${DB_NAME:?DB_NAME is required}"

guard_prod_danger

printf '[mod.install] module=%s db=%s\n' "$MODULE" "$DB_NAME"

compose_dev run --rm -T \
  -e SC_SEED_ENABLED \
  -e SC_SEED_PROFILE \
  -e SC_SEED_STEPS \
  -e SC_BOOTSTRAP_MODE \
  -e SC_BOOTSTRAP_USERS \
  -e SC_BOOTSTRAP_ADMIN_LOGIN \
  -e SC_BOOTSTRAP_ADMIN_PASSWORD \
  -e SC_BOOTSTRAP_ADMIN_NAME \
  -e SC_BOOTSTRAP_ADMIN_GROUP_XMLIDS \
  -e SC_BOOTSTRAP_ADMIN_COMPANY_MODE \
  -e SC_BOOTSTRAP_UPDATE_PASSWORD \
  --entrypoint /usr/bin/odoo odoo \
  --config="$ODOO_CONF" \
  -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path=/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,"$ADDONS_EXTERNAL_MOUNT" \
  -i "$MODULE" \
  ${WITHOUT_DEMO:-} \
  --no-http --workers=0 --max-cron-threads=0 \
  --stop-after-init ${ODOO_ARGS:-} </dev/null
