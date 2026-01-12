#!/usr/bin/env bash
set -euo pipefail

# Require ROOT_DIR for safety
: "${ROOT_DIR:?ROOT_DIR is required}"

# SOT: load .env for both make and direct script invocation
ENV_FILE="${ROOT_DIR}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "❌ missing .env at ${ENV_FILE}" >&2
  echo "   Fix: cp .env.example .env" >&2
  exit 2
fi

# shellcheck disable=SC1090
set -a
source "${ENV_FILE}"
set +a

# Compose + projects
COMPOSE_BIN="${COMPOSE_BIN:-docker compose}"
PROJECT_CI="${PROJECT_CI:-sc-ci}"

# ---- Compose project name: single source of truth ----
if [[ -n "${PROJECT:-}" && -n "${COMPOSE_PROJECT_NAME:-}" && "${PROJECT}" != "${COMPOSE_PROJECT_NAME}" ]]; then
  echo "[FATAL] PROJECT(${PROJECT}) != COMPOSE_PROJECT_NAME(${COMPOSE_PROJECT_NAME})" >&2
  exit 2
fi

: "${COMPOSE_PROJECT_NAME:?COMPOSE_PROJECT_NAME required (export it or set in .env)}"

# keep PROJECT as alias for legacy scripts (do not set independently)
PROJECT="${COMPOSE_PROJECT_NAME}"
export COMPOSE_PROJECT_NAME PROJECT

# DB/module
DB_NAME="${DB_NAME:-${DB:-}}"
DB_CI="${DB_CI:-sc_test}"
DB_USER="${DB_USER:-}"
MODULE="${MODULE:-smart_construction_core}"
ODOO_CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

# required env gate (fail fast when scripts run directly)
_req_vars=(COMPOSE_PROJECT_NAME DB_USER DB_PASSWORD DB_NAME ADMIN_PASSWD JWT_SECRET ODOO_DBFILTER)
_missing=()
for _k in "${_req_vars[@]}"; do
  if [[ -z "${!_k:-}" ]]; then
    _missing+=("$_k")
  fi
done
if [[ "${#_missing[@]}" -gt 0 ]]; then
  echo "❌ missing required env vars: ${_missing[*]}" >&2
  echo "   Fix: cp .env.example .env  (and fill values)" >&2
  exit 2
fi

# Tags
TEST_TAGS="${TEST_TAGS:-sc_smoke,sc_gate}"
TEST_TAGS_FINAL="${TEST_TAGS_FINAL:-/${MODULE}:sc_smoke,/${MODULE}:sc_gate}"

# CI outputs
CI_LOG="${CI_LOG:-test-ci.log}"
CI_ARTIFACT_DIR="${CI_ARTIFACT_DIR:-artifacts/ci}"
CI_PASS_SIG_RE="${CI_PASS_SIG_RE:-(0 failed, 0 error\\(s\\))}"
CI_ARTIFACT_PURGE="${CI_ARTIFACT_PURGE:-1}"
CI_ARTIFACT_KEEP="${CI_ARTIFACT_KEEP:-30}"
CI_TAIL_ODOO="${CI_TAIL_ODOO:-2000}"
CI_TAIL_DB="${CI_TAIL_DB:-800}"
CI_TAIL_REDIS="${CI_TAIL_REDIS:-400}"

export COMPOSE_ANSI="${COMPOSE_ANSI:-never}"
export MSYS_NO_PATHCONV="${MSYS_NO_PATHCONV:-1}"
export MSYS2_ARG_CONV_EXCL="${MSYS2_ARG_CONV_EXCL:---test-tags}"
export ODOO_CONF
