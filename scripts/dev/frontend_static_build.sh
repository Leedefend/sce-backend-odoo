#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
ENV_NAME="${ENV:-dev}"
ENV_FILE="${ENV_FILE:-${ROOT_DIR}/.env.${ENV_NAME}}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "frontend static build env file not found: ${ENV_FILE}" >&2
  exit 2
fi

_pre_DB_NAME="${DB_NAME:-}"
_pre_VITE_ODOO_DB="${VITE_ODOO_DB:-}"
_pre_VITE_APP_ENV="${VITE_APP_ENV:-}"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

[[ -n "${_pre_DB_NAME}" ]] && DB_NAME="${_pre_DB_NAME}"
[[ -n "${_pre_VITE_ODOO_DB}" ]] && VITE_ODOO_DB="${_pre_VITE_ODOO_DB}"
[[ -n "${_pre_VITE_APP_ENV}" ]] && VITE_APP_ENV="${_pre_VITE_APP_ENV}"

: "${DB_NAME:?DB_NAME is required for frontend static build}"

export VITE_ODOO_DB="${VITE_ODOO_DB:-${DB_NAME}}"
export VITE_APP_ENV="${VITE_APP_ENV:-${ENV_NAME}}"

echo "[frontend.static.build] env_file=${ENV_FILE} vite_db=${VITE_ODOO_DB} app_env=${VITE_APP_ENV}"
cd "${ROOT_DIR}"
exec pnpm -C frontend/apps/web build
