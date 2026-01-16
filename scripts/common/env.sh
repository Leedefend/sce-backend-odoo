#!/usr/bin/env bash
set -euo pipefail

# Require ROOT_DIR for safety
: "${ROOT_DIR:?ROOT_DIR is required}"

# =========================================================
# Load .env (Single Source of Truth for defaults)
# BUT: externally provided vars (Makefile / CLI) must win
# =========================================================

ENV_NAME="${ENV:-}"
ENV_FILE="${ENV_FILE:-}"
if [[ -z "${ENV_FILE}" && -n "${ENV_NAME}" ]]; then
  ENV_FILE="${ROOT_DIR}/.env.${ENV_NAME}"
fi
if [[ -z "${ENV_FILE}" ]]; then
  ENV_FILE="${ROOT_DIR}/.env"
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "❌ missing env file at ${ENV_FILE}" >&2
  echo "   Fix: cp .env.example .env  or  cp .env.example .env.<env>" >&2
  exit 2
fi

# ---- Snapshot externally provided vars (highest priority) ----
_pre_DB_NAME="${DB_NAME:-}"
_pre_DB="${DB:-}"
_pre_DB_USER="${DB_USER:-}"
_pre_DB_PASSWORD="${DB_PASSWORD:-}"
_pre_MODULE="${MODULE:-}"
_pre_COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-}"
_pre_PROJECT="${PROJECT:-}"
_pre_ODOO_CONF="${ODOO_CONF:-}"
_pre_BD="${BD:-}"

# ---- Load .env defaults ----
# shellcheck disable=SC1090
set -a
source "${ENV_FILE}"
set +a

# ---- Restore external overrides (do NOT let .env override them) ----
[[ -n "${_pre_DB_NAME}" ]] && DB_NAME="${_pre_DB_NAME}"
[[ -n "${_pre_DB}" ]] && DB="${_pre_DB}"
[[ -n "${_pre_DB_USER}" ]] && DB_USER="${_pre_DB_USER}"
[[ -n "${_pre_DB_PASSWORD}" ]] && DB_PASSWORD="${_pre_DB_PASSWORD}"
[[ -n "${_pre_MODULE}" ]] && MODULE="${_pre_MODULE}"
[[ -n "${_pre_COMPOSE_PROJECT_NAME}" ]] && COMPOSE_PROJECT_NAME="${_pre_COMPOSE_PROJECT_NAME}"
[[ -n "${_pre_PROJECT}" ]] && PROJECT="${_pre_PROJECT}"
[[ -n "${_pre_ODOO_CONF}" ]] && ODOO_CONF="${_pre_ODOO_CONF}"
[[ -n "${_pre_BD}" ]] && BD="${_pre_BD}"

# =========================================================
# Compose / Project identity (Single Source of Truth)
# =========================================================

COMPOSE_BIN="${COMPOSE_BIN:-docker compose}"
PROJECT_CI="${PROJECT_CI:-sc-ci}"

# PROJECT and COMPOSE_PROJECT_NAME must be identical if both exist
if [[ -n "${PROJECT:-}" && -n "${COMPOSE_PROJECT_NAME:-}" && "${PROJECT}" != "${COMPOSE_PROJECT_NAME}" ]]; then
  echo "[FATAL] PROJECT(${PROJECT}) != COMPOSE_PROJECT_NAME(${COMPOSE_PROJECT_NAME})" >&2
  exit 2
fi

: "${COMPOSE_PROJECT_NAME:?COMPOSE_PROJECT_NAME required (export it or set in .env)}"

# Keep PROJECT as alias for legacy scripts
PROJECT="${COMPOSE_PROJECT_NAME}"
export COMPOSE_PROJECT_NAME PROJECT

# =========================================================
# DB / Module resolution
# =========================================================

# DB_NAME priority:
# 1) externally provided DB_NAME
# 2) externally provided DB
# 3) externally provided BD (legacy alias)
# 4) .env DB_NAME
DB_NAME="${DB_NAME:-${DB:-${BD:-}}}"

DB_CI="${DB_CI:-sc_test}"
DB_USER="${DB_USER:-}"
MODULE="${MODULE:-smart_construction_core}"
ODOO_CONF="${ODOO_CONF:-/var/lib/odoo/odoo.conf}"

# =========================================================
# Required env gate (fail fast)
# =========================================================

_req_vars=(
  COMPOSE_PROJECT_NAME
  DB_USER
  DB_PASSWORD
  DB_NAME
  ADMIN_PASSWD
  JWT_SECRET
  ODOO_DBFILTER
)

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

# =========================================================
# Test / CI defaults
# =========================================================

TEST_TAGS="${TEST_TAGS:-sc_smoke,sc_gate}"
TEST_TAGS_FINAL="${TEST_TAGS_FINAL:-/${MODULE}:sc_smoke,/${MODULE}:sc_gate}"

CI_LOG="${CI_LOG:-test-ci.log}"
CI_ARTIFACT_DIR="${CI_ARTIFACT_DIR:-artifacts/ci}"
CI_PASS_SIG_RE="${CI_PASS_SIG_RE:-(0 failed, 0 error\\(s\\))}"
CI_ARTIFACT_PURGE="${CI_ARTIFACT_PURGE:-1}"
CI_ARTIFACT_KEEP="${CI_ARTIFACT_KEEP:-30}"
CI_TAIL_ODOO="${CI_TAIL_ODOO:-2000}"
CI_TAIL_DB="${CI_TAIL_DB:-800}"
CI_TAIL_REDIS="${CI_TAIL_REDIS:-400}"

# =========================================================
# Shell / platform hygiene
# =========================================================

export COMPOSE_ANSI="${COMPOSE_ANSI:-never}"
export MSYS_NO_PATHCONV="${MSYS_NO_PATHCONV:-1}"
export MSYS2_ARG_CONV_EXCL="${MSYS2_ARG_CONV_EXCL:---test-tags}"
export ODOO_CONF
