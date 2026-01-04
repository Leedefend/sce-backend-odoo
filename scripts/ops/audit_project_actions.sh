#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
export ROOT_DIR

# shellcheck source=../common/env.sh
source "$ROOT_DIR/scripts/common/env.sh"
# shellcheck source=../common/compose.sh
source "$ROOT_DIR/scripts/common/compose.sh"

: "${DB_NAME:?DB_NAME is required}"
: "${DB_USER:?DB_USER is required}"

OUT="${OUT:-docs/audit/action_groups_missing_db.csv}"
ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"
AUDIT_OUT="${AUDIT_OUT:-/tmp/sc_audit_project_actions.csv}"

mkdir -p "$(dirname "$OUT")"

compose_dev exec -T -e AUDIT_OUT="$AUDIT_OUT" odoo odoo shell -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
  --logfile=/dev/null --log-level=warn \
<<'PY'
import csv
import os

def xmlid_for(record):
    data = env["ir.model.data"].sudo().search([
        ("model", "=", record._name),
        ("res_id", "=", record.id),
        ("module", "!=", False),
    ], order="module asc, name asc, id asc", limit=1)
    if not data:
        return ""
    return f"{data.module}.{data.name}"

def group_xmlids(groups):
    if not groups:
        return []
    data = env["ir.model.data"].sudo().search([
        ("model", "=", "res.groups"),
        ("res_id", "in", groups.ids),
        ("module", "!=", False),
    ], order="module asc, name asc, id asc")
    mapping = {}
    for d in data:
        mapping.setdefault(d.res_id, f"{d.module}.{d.name}")
    return [mapping.get(g.id, str(g.id)) for g in groups]

def is_sc_group(xmlid):
    return xmlid.startswith("smart_construction_core.group_sc_")

ProjectModel = env["ir.model"].sudo().search([("model", "=", "project.project")], limit=1)
act_windows = []
act_servers = []
if ProjectModel:
    act_windows = env["ir.actions.act_window"].sudo().search([
        ("binding_model_id", "=", ProjectModel.id),
    ])
    act_servers = env["ir.actions.server"].sudo().search([
        ("binding_model_id", "=", ProjectModel.id),
    ])

rows = []
for act in act_windows:
    groups = group_xmlids(act.groups_id)
    rows.append([
        "act_window",
        xmlid_for(act),
        act.name or "",
        act.res_model or "",
        act.binding_type or "",
        "1" if any(is_sc_group(x) for x in groups) else "0",
        ";".join(groups),
    ])

for act in act_servers:
    groups = group_xmlids(act.groups_id)
    rows.append([
        "act_server",
        xmlid_for(act),
        act.name or "",
        "",
        act.binding_type or "",
        "1" if any(is_sc_group(x) for x in groups) else "0",
        ";".join(groups),
    ])

out_path = os.environ.get("AUDIT_OUT", "/tmp/sc_audit_project_actions.csv")
with open(out_path, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["action_type", "xmlid", "name", "res_model", "binding_type", "has_sc_group", "groups"])
    for r in rows:
        writer.writerow(r)
print(out_path)
PY

compose_dev exec -T odoo cat "$AUDIT_OUT" >"$OUT"
echo "[audit.project.actions] wrote ${OUT}"
