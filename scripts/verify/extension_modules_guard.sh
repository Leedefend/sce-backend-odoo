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

psql_cmd() {
  compose ${COMPOSE_FILES} exec -T db psql -U "${DB_USER}" -d "${DB_NAME}" -At -c "$1"
}

raw_value="$(psql_cmd "SELECT COALESCE(value, '') FROM ir_config_parameter WHERE key='sc.core.extension_modules' LIMIT 1;")"
normalized="${raw_value// /}"

required_modules=(
  "smart_construction_core"
  "smart_construction_portal"
)
missing_modules=()
for mod in "${required_modules[@]}"; do
  if [[ ",${normalized}," != *",${mod},"* ]]; then
    missing_modules+=("${mod}")
  fi
done

if [[ ${#missing_modules[@]} -eq 0 ]]; then
  echo "[verify.extension_modules.guard] PASS db=${DB_NAME} value=${raw_value}"
  exit 0
fi

echo "[verify.extension_modules.guard] FAIL db=${DB_NAME} key=sc.core.extension_modules missing ${missing_modules[*]}" >&2
echo "[verify.extension_modules.guard] HINT run: make policy.apply.extension_modules DB_NAME=${DB_NAME}" >&2
echo "[verify.extension_modules.guard] HINT then restart: make restart" >&2
exit 1
