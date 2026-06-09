#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

DB_NAME="${DB_NAME:-${DB:-sc_demo}}"

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/guard_prod.sh
source "$ROOT_DIR/scripts/common/guard_prod.sh"

guard_prod_forbid

: "${DB_NAME:?DB_NAME is required}"

checks=(
  "core_document_processing:scripts/ops/validate_core_document_processing_gate.sh"
  "business_flow_closure:scripts/ops/validate_business_flow_closure.sh"
  "business_action_coverage:scripts/ops/validate_business_action_coverage.sh"
  "field_operation_actions:scripts/ops/validate_field_operation_actions.sh"
)

started_at="$(date -Iseconds)"
echo "BUSINESS_CAPABILITY_GATE_START: db=${DB_NAME} started_at=${started_at}"

for check in "${checks[@]}"; do
  name="${check%%:*}"
  script="${check#*:}"
  echo "BUSINESS_CAPABILITY_GATE_CHECK_START: ${name}"
  DB_NAME="$DB_NAME" "$ROOT_DIR/$script"
  echo "BUSINESS_CAPABILITY_GATE_CHECK_PASS: ${name}"
done

finished_at="$(date -Iseconds)"
echo "BUSINESS_CAPABILITY_GATE_RESULT: PASS db=${DB_NAME} started_at=${started_at} finished_at=${finished_at}"
