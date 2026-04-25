#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-}"
if [[ -z "$DB_NAME" ]]; then
  echo "❌ DB_NAME is required" >&2
  exit 2
fi

ENV_FORWARD_ARGS=()
for env_name in MIGRATION_REPO_ROOT MIGRATION_REPLAY_DB_ALLOWLIST MIGRATION_ARTIFACT_ROOT; do
  if [[ -n "${!env_name:-}" ]]; then
    ENV_FORWARD_ARGS+=("-e" "${env_name}=${!env_name}")
  fi
done

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T "${ENV_FORWARD_ARGS[@]}" odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf
