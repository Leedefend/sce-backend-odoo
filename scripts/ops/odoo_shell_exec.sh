#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/../_lib/common.sh"

DB_NAME="${DB_NAME:-}"
if [[ -z "$DB_NAME" ]]; then
  echo "❌ DB_NAME is required" >&2
  exit 2
fi

ENV_FORWARD_ARGS=()
while IFS='=' read -r env_name _; do
  case "$env_name" in
    MIGRATION_*|FRESH_DB_*|LEGACY_USER_*|PROJECT_ANCHOR_*|BUSINESS_FACT_*|CONSTRUCTION_CONTRACT_*|SUPPLIER_CONTRACT_*|PARTNER_ASSET_XML|PARTNER_BUSINESS_ALIGNED_GATE_CSV|PARTNER_FACT_ALIGNMENT_*|PARTNER_PROFILE_BACKFILL_*|PARTNER_SOURCE_CREATOR_*)
      if [[ -n "${!env_name:-}" ]]; then
        ENV_FORWARD_ARGS+=("-e" "${env_name}=${!env_name}")
      fi
      ;;
  esac
done < <(env)

# shellcheck disable=SC2086
compose ${COMPOSE_FILES} exec -T "${ENV_FORWARD_ARGS[@]}" odoo odoo shell -d "$DB_NAME" -c /var/lib/odoo/odoo.conf
