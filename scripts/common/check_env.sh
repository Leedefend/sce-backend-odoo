#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

ENV_NAME="${ENV:-}"
ENV_FILE="${ENV_FILE:-}"
if [[ -z "${ENV_FILE}" && -n "${ENV_NAME}" ]]; then
  ENV_FILE="${ROOT_DIR}/.env.${ENV_NAME}"
fi
if [[ -z "${ENV_FILE}" ]]; then
  ENV_FILE="${ROOT_DIR}/.env"
fi

# Load env file as SOT if present (do NOT fail here; fail below with clear message)
if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

missing=()

need() {
  local k="$1"
  if [[ -z "${!k:-}" ]]; then
    missing+=("$k")
  fi
}

need COMPOSE_PROJECT_NAME
need DB_USER
need DB_PASSWORD
need DB_NAME
need ADMIN_PASSWD
need JWT_SECRET
need ODOO_DBFILTER

if (( ${#missing[@]} > 0 )); then
  echo "❌ missing required env vars: ${missing[*]}" >&2
  echo "   Fix: cp .env.example .env  (or .env.<env>) and fill required values." >&2
  exit 2
fi

# lightweight sanity checks
if [[ "${ODOO_DBFILTER}" != ^* ]]; then
  echo "⚠️  ODOO_DBFILTER does not start with '^' (got: ${ODOO_DBFILTER}). This may allow unexpected DBs." >&2
fi
