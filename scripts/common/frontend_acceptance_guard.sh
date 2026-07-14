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
