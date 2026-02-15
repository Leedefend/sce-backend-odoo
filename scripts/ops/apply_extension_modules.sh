#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

source "$ROOT_DIR/scripts/common/env.sh"
source "$ROOT_DIR/scripts/common/guard_prod.sh"
source "$ROOT_DIR/scripts/_lib/common.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME required}"
: "${DB_USER:?DB_USER required}"
: "${COMPOSE_FILES:?COMPOSE_FILES required}"
TRACE_ID="extmods_$(date +%Y%m%d%H%M%S)_$RANDOM"

psql_exec() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -v ON_ERROR_STOP=1 -q -c "$1"
}

psql_query() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -At -c "$1"
}

before_value="$(psql_query "SELECT COALESCE(value, '') FROM ir_config_parameter WHERE key='sc.core.extension_modules' LIMIT 1;")"

required_modules=(
  "smart_construction_core"
  "smart_construction_portal"
)

for mod in "${required_modules[@]}"; do
  psql_exec "
  INSERT INTO ir_config_parameter (key, value, create_uid, create_date, write_uid, write_date)
  VALUES ('sc.core.extension_modules', '${mod}', 1, NOW(), 1, NOW())
  ON CONFLICT (key) DO UPDATE
  SET value = CASE
    WHEN POSITION('${mod}' IN COALESCE(ir_config_parameter.value, '')) > 0
      THEN COALESCE(ir_config_parameter.value, '')
    WHEN COALESCE(ir_config_parameter.value, '') = ''
      THEN '${mod}'
    ELSE COALESCE(ir_config_parameter.value, '') || ',${mod}'
  END,
  write_uid = 1,
  write_date = NOW();
  "
done

after_value="$(psql_query "SELECT COALESCE(value, '') FROM ir_config_parameter WHERE key='sc.core.extension_modules' LIMIT 1;")"
normalized="${after_value// /}"
if [[ ",${normalized}," != *",smart_construction_core,"* || ",${normalized}," != *",smart_construction_portal,"* ]]; then
  echo "[policy.apply.extension_modules] FAIL db=${DB_NAME} trace_id=${TRACE_ID} old=${before_value} new=${after_value}" >&2
  exit 1
fi

echo "[policy.apply.extension_modules] PASS db=${DB_NAME} trace_id=${TRACE_ID} old=${before_value} new=${after_value}"
echo "[policy.apply.extension_modules] NEXT restart odoo to reload extension loader cache: make restart"
