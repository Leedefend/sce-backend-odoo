#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"

# Load .env as SOT if present (do NOT fail here; fail below with clear message)
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
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
  echo "   Fix: cp .env.example .env and fill required values." >&2
  exit 2
fi

# lightweight sanity checks
if [[ "${ODOO_DBFILTER}" != ^* ]]; then
  echo "⚠️  ODOO_DBFILTER does not start with '^' (got: ${ODOO_DBFILTER}). This may allow unexpected DBs." >&2
fi
