#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/_lib/common.sh"

: "${DB_NAME:?DB_NAME is required}"
: "${COMPOSE_FILES:=-f docker-compose.yml}"

printf '[platform.init.preflight] apply baseline db=%s\n' "$DB_NAME"

compose ${COMPOSE_FILES} exec -T odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf <<'PY'
Init = env["sc.platform.initialization"]  # noqa: F821
Init.apply_baseline()
Init.assert_baseline_ready()
env.cr.commit()  # noqa: F821
print("PLATFORM_INIT_PREFLIGHT=PASS")
PY
