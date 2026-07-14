#!/usr/bin/env bash
set -euo pipefail

readonly FRONTEND_ACCEPTANCE_DB_NAME="sc_frontend_acceptance"

guard_frontend_acceptance_scope() {
  if [[ "${DB_NAME:-}" != "$FRONTEND_ACCEPTANCE_DB_NAME" ]]; then
    echo "[DENY] frontend acceptance fixture requires DB_NAME=${FRONTEND_ACCEPTANCE_DB_NAME} (got ${DB_NAME:-<empty>})" >&2
    return 20
  fi
  if [[ "${SC_ENVIRONMENT:-}" != "acceptance" ]]; then
    echo "[DENY] frontend acceptance fixture requires SC_ENVIRONMENT=acceptance" >&2
    return 21
  fi
  if [[ "${SC_ALLOW_DEMO_DATA:-}" != "1" ]]; then
    echo "[DENY] frontend acceptance fixture requires SC_ALLOW_DEMO_DATA=1" >&2
    return 22
  fi
}

acquire_frontend_acceptance_lock() {
  local operation="${1:?operation required}"
  local lock_dir="${ROOT_DIR:-$(pwd)}/.runtime/frontend-acceptance"
  mkdir -p "$lock_dir"
  local lock_file="$lock_dir/${FRONTEND_ACCEPTANCE_DB_NAME}-${operation}.lock"
  exec 9>"$lock_file"
  if ! flock -n 9; then
    echo "[DENY] frontend acceptance ${operation} already running for database=${FRONTEND_ACCEPTANCE_DB_NAME}" >&2
    return 23
  fi
}
