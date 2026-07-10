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
_pre_FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-}"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

[[ -n "${_pre_DB_NAME}" ]] && DB_NAME="${_pre_DB_NAME}"
[[ -n "${_pre_VITE_ODOO_DB}" ]] && VITE_ODOO_DB="${_pre_VITE_ODOO_DB}"
[[ -n "${_pre_VITE_APP_ENV}" ]] && VITE_APP_ENV="${_pre_VITE_APP_ENV}"
[[ -n "${_pre_FRONTEND_DIST_DIR}" ]] && FRONTEND_DIST_DIR="${_pre_FRONTEND_DIST_DIR}"

: "${DB_NAME:?DB_NAME is required for frontend static build}"

export VITE_ODOO_DB="${VITE_ODOO_DB:-${DB_NAME}}"
export VITE_APP_ENV="${VITE_APP_ENV:-${ENV_NAME}}"
case "${ENV_NAME}" in
  prod|production)
    VITE_BUILD_MODE="${VITE_BUILD_MODE:-production}"
    ;;
  dev|daily|development)
    VITE_BUILD_MODE="${VITE_BUILD_MODE:-development}"
    ;;
  *)
    VITE_BUILD_MODE="${VITE_BUILD_MODE:-${ENV_NAME}}"
    ;;
esac
FRONTEND_DIST_DIR="${FRONTEND_DIST_DIR:-frontend/apps/web/dist}"
case "${FRONTEND_DIST_DIR}" in
  /*) FRONTEND_DIST_ABS="${FRONTEND_DIST_DIR}" ;;
  ./*) FRONTEND_DIST_ABS="${ROOT_DIR}/${FRONTEND_DIST_DIR#./}" ;;
  *) FRONTEND_DIST_ABS="${ROOT_DIR}/${FRONTEND_DIST_DIR}" ;;
esac
export VITE_BUILD_OUT_DIR="${FRONTEND_DIST_ABS}"

echo "[frontend.static.build] env_file=${ENV_FILE} vite_db=${VITE_ODOO_DB} app_env=${VITE_APP_ENV} mode=${VITE_BUILD_MODE} out_dir=${VITE_BUILD_OUT_DIR}"
mkdir -p "${FRONTEND_DIST_ABS}"
find "${FRONTEND_DIST_ABS}" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cd "${ROOT_DIR}"
"${ROOT_DIR}/scripts/dev/pnpm_exec.sh" -C frontend/apps/web exec vite build --mode "${VITE_BUILD_MODE}"

if [[ "${ENV_NAME}" != "prod" && "${ENV_NAME}" != "production" ]]; then
  if grep -Rqs '"sc_prod"' "${FRONTEND_DIST_ABS}/assets"; then
    echo "frontend static build produced sc_prod in non-prod env=${ENV_NAME}; refuse to publish" >&2
    exit 1
  fi
fi
