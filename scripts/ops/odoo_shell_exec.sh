#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-}"
if [[ -z "$DB_NAME" ]]; then
  echo "❌ DB_NAME is required" >&2
  exit 2
fi

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf
