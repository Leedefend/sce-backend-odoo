#!/usr/bin/env bash
set -euo pipefail

# Require ROOT_DIR for safety
: "${ROOT_DIR:?ROOT_DIR is required}"

# Compose + projects
COMPOSE_BIN="${COMPOSE_BIN:-docker compose}"
PROJECT_CI="${PROJECT_CI:-sc-ci}"

# ---- Compose project name: single source of truth ----
if [[ -n "${PROJECT:-}" && -n "${COMPOSE_PROJECT_NAME:-}" && "${PROJECT}" != "${COMPOSE_PROJECT_NAME}" ]]; then
  echo "[FATAL] PROJECT(${PROJECT}) != COMPOSE_PROJECT_NAME(${COMPOSE_PROJECT_NAME})" >&2
  exit 2
fi

# allow .env to provide it (server & local)
if [[ -z "${COMPOSE_PROJECT_NAME:-}" && -f "${ROOT_DIR}/.env" ]]; then
  # shellcheck disable=SC1090
  source "${ROOT_DIR}/.env"
fi

: "${COMPOSE_PROJECT_NAME:?COMPOSE_PROJECT_NAME required (export it or set in .env)}"

# keep PROJECT as alias for legacy scripts (do not set independently)
PROJECT="${COMPOSE_PROJECT_NAME}"
export COMPOSE_PROJECT_NAME PROJECT

# DB/module
DB_NAME="${DB_NAME:-${DB:-sc_odoo}}"
DB_CI="${DB_CI:-sc_test}"
DB_USER="${DB_USER:-odoo}"
MODULE="${MODULE:-smart_construction_core}"
ODOO_CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

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
