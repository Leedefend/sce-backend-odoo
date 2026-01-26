#!/usr/bin/env bash
set -euo pipefail

DB_NAME="${DB_NAME:-sc_demo}"
OUTDIR="${OUTDIR:-/tmp/smart_core_verify}"
CONFIG="${ODOO_CONF:-/etc/odoo/odoo.conf}"

mkdir -p "$OUTDIR"

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case smart_core_project_kanban_lifecycle_pm \
  --op action_open \
  --model project.project \
  --view_type kanban \
  --action_xmlid smart_construction_core.action_sc_project_kanban_lifecycle \
  --include_meta \
  --config "$CONFIG" \
  --outdir "$OUTDIR"

scripts/contract/snapshot_export.sh \
  --db "$DB_NAME" \
  --user pm \
  --case smart_core_portal_lifecycle_dashboard_pm \
  --op ui.contract \
  --route /portal/lifecycle \
  --trace_id smart_core_verify \
  --config "$CONFIG" \
  --outdir "$OUTDIR"

echo "[verify.smart_core] PASS outdir=$OUTDIR"
