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

OUT_DIR="${OUT_DIR:-docs/audit}"
OUT_ACTIONS_ALL="${OUT_ACTIONS_ALL:-${OUT_DIR}/action_list_all.csv}"
OUT_ACTIONS_MISSING="${OUT_ACTIONS_MISSING:-${OUT_DIR}/action_groups_missing_db.csv}"
OUT_ACTION_VIS="${OUT_ACTION_VIS:-${OUT_DIR}/action_visibility_by_role.csv}"
OUT_ACTION_VERDICTS="${OUT_ACTION_VERDICTS:-${OUT_DIR}/action_verdict_candidates.csv}"
OUT_ACTION_REFS="${OUT_ACTION_REFS:-${OUT_DIR}/action_references.csv}"
ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"
TMP_ACTIONS="${TMP_ACTIONS:-/tmp/sc_audit_project_actions.csv}"
TMP_VIS="${TMP_VIS:-/tmp/sc_audit_action_visibility.csv}"
TMP_MISSING="${TMP_MISSING:-/tmp/sc_audit_action_missing.csv}"
TMP_MENU_REFS="${TMP_MENU_REFS:-/tmp/sc_audit_action_menu_refs.csv}"
TMP_VIEW_REFS="${TMP_VIEW_REFS:-/tmp/sc_audit_action_view_refs.csv}"
HOST_MENU_REFS="${HOST_MENU_REFS:-/tmp/sc_audit_action_menu_refs_host.csv}"

mkdir -p "$OUT_DIR"

compose_dev exec -T \
  -e TMP_ACTIONS="$TMP_ACTIONS" \
  -e TMP_VIS="$TMP_VIS" \
  -e TMP_MISSING="$TMP_MISSING" \
  -e TMP_MENU_REFS="$TMP_MENU_REFS" \
  odoo odoo shell -d "$DB_NAME" \
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

def user_groups_by_login(env, login):
    user = env["res.users"].sudo().with_context(active_test=False).search([("login", "=", login)], limit=1)
    if not user:
        return None, set(), []
    groups = user.groups_id.sudo()
    return user, set(groups.ids), group_xmlids(groups)

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

actions = []
action_xmlid_by_id = {}
for act in act_windows:
    groups = group_xmlids(act.groups_id)
    group_ids = set(act.groups_id.ids)
    action_xmlid = xmlid_for(act)
    actions.append({
        "action_type": "act_window",
        "id": act.id,
        "xmlid": action_xmlid,
        "name": act.name or "",
        "res_model": act.res_model or "",
        "view_mode": act.view_mode or "",
        "binding_type": act.binding_type or "",
        "groups": groups,
        "group_ids": group_ids,
        "has_sc_group": any(is_sc_group(x) for x in groups),
        "has_groups": bool(groups),
    })
    if action_xmlid:
        action_xmlid_by_id[act.id] = action_xmlid

for act in act_servers:
    groups = group_xmlids(act.groups_id)
    group_ids = set(act.groups_id.ids)
    actions.append({
        "action_type": "act_server",
        "id": act.id,
        "xmlid": xmlid_for(act),
        "name": act.name or "",
        "res_model": "",
        "view_mode": "",
        "binding_type": act.binding_type or "",
        "groups": groups,
        "group_ids": group_ids,
        "has_sc_group": any(is_sc_group(x) for x in groups),
        "has_groups": bool(groups),
    })

tmp_actions = os.environ.get("TMP_ACTIONS", "/tmp/sc_audit_project_actions.csv")
with open(tmp_actions, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow([
        "action_type",
        "action_id",
        "xmlid",
        "name",
        "res_model",
        "view_mode",
        "binding_type",
        "has_sc_group",
        "groups",
    ])
    for a in actions:
        writer.writerow([
            a["action_type"],
            a["id"],
            a["xmlid"],
            a["name"],
            a["res_model"],
            a["view_mode"],
            a["binding_type"],
            "1" if a["has_sc_group"] else "0",
            ";".join(a["groups"]),
        ])

roles = ["demo_pm", "demo_cost", "demo_readonly", "admin"]
role_groups = {}
for r in roles:
    user, ids, xmlids = user_groups_by_login(env, r)
    role_groups[r] = {
        "user_found": bool(user),
        "ids": ids,
        "xmlids": xmlids,
    }

tmp_vis = os.environ.get("TMP_VIS", "/tmp/sc_audit_action_visibility.csv")
with open(tmp_vis, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow([
        "role",
        "action_xmlid",
        "action_name",
        "res_model",
        "view_mode",
        "has_groups",
        "groups_xmlids",
        "visible",
    ])
    for r in roles:
        r_groups = role_groups.get(r, {})
        r_ids = r_groups.get("ids", set())
        user_found = r_groups.get("user_found", False)
        for a in actions:
            visible = False
            if user_found:
                if not a["has_groups"]:
                    visible = True
                else:
                    visible = bool(set(r_ids) & set(a.get("group_ids", set())))
            writer.writerow([
                r,
                a["xmlid"],
                a["name"],
                a["res_model"],
                a["view_mode"],
                "1" if a["has_groups"] else "0",
                ";".join(a["groups"]),
                "1" if visible else "0",
            ])

tmp_missing = os.environ.get("TMP_MISSING", "/tmp/sc_audit_action_missing.csv")
with open(tmp_missing, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["action_type", "xmlid", "name", "res_model", "view_mode", "binding_type", "has_sc_group", "groups"])
    for a in actions:
        if a["has_groups"]:
            continue
        writer.writerow([
            a["action_type"],
            a["xmlid"],
            a["name"],
            a["res_model"],
            a["view_mode"],
            a["binding_type"],
            "1" if a["has_sc_group"] else "0",
            ";".join(a["groups"]),
        ])

tmp_menu_refs = os.environ.get("TMP_MENU_REFS", "/tmp/sc_audit_action_menu_refs.csv")
with open(tmp_menu_refs, "w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["action_xmlid", "ref_type", "ref_name", "ref_xmlid", "ref_source"])
    menus = env["ir.ui.menu"].sudo().search([("action", "!=", False)])
    for m in menus:
        action_ref = m.action
        if not action_ref:
            continue
        action_id = None
        action_source = ""
        if isinstance(action_ref, str):
            if not action_ref.startswith("ir.actions.act_window,"):
                continue
            try:
                action_id = int(action_ref.split(",")[1])
            except Exception:
                continue
            action_source = action_ref
        else:
            if getattr(action_ref, "_name", "") != "ir.actions.act_window":
                continue
            action_id = action_ref.id
            action_source = f"{action_ref._name},{action_id}"
        action_xmlid = action_xmlid_by_id.get(action_id, "")
        if not action_xmlid:
            continue
        writer.writerow([
            action_xmlid,
            "menu",
            m.name or "",
            xmlid_for(m),
            action_source,
        ])
PY

compose_dev exec -T odoo cat "$TMP_MISSING" >"$OUT_ACTIONS_MISSING"
compose_dev exec -T odoo cat "$TMP_ACTIONS" >"$OUT_ACTIONS_ALL"
compose_dev exec -T odoo cat "$TMP_VIS" >"$OUT_ACTION_VIS"
compose_dev exec -T odoo cat "$TMP_MENU_REFS" >"$HOST_MENU_REFS"

if command -v rg >/dev/null 2>&1; then
  rg -n --glob 'addons/**/views/**/*.xml' '%\\([A-Za-z0-9_]+\\.[A-Za-z0-9_]+\\)d' "$ROOT_DIR" > /tmp/sc_audit_action_view_refs_raw.txt || true
  TMP_VIEW_REFS="$TMP_VIEW_REFS" python3 - <<'PY'
import csv
import re
import os
from pathlib import Path

raw_path = Path("/tmp/sc_audit_action_view_refs_raw.txt")
out_path = Path(os.environ.get("TMP_VIEW_REFS", "/tmp/sc_audit_action_view_refs.csv"))
pattern = re.compile(r"%\(([A-Za-z0-9_]+\.[A-Za-z0-9_]+)\)d")

rows = []
if raw_path.exists():
    for line in raw_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        try:
            file_path, line_no, text = line.split(":", 2)
        except ValueError:
            continue
        for m in pattern.findall(text):
            rows.append([m, "view_button", "", "", f"{file_path}:{line_no}"])

with out_path.open("w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["action_xmlid", "ref_type", "ref_name", "ref_xmlid", "ref_source"])
    for r in rows:
        writer.writerow(r)
PY
else
  printf "action_xmlid,ref_type,ref_name,ref_xmlid,ref_source\n" >"$TMP_VIEW_REFS"
fi

{
  head -n 1 "$HOST_MENU_REFS" 2>/dev/null || echo "action_xmlid,ref_type,ref_name,ref_xmlid,ref_source"
  tail -n +2 "$HOST_MENU_REFS" 2>/dev/null || true
  if [ -f "$TMP_VIEW_REFS" ]; then
    tail -n +2 "$TMP_VIEW_REFS"
  fi
} >"$OUT_ACTION_REFS"

python3 - <<'PY'
import csv
import re
from pathlib import Path

all_actions_path = Path("docs/audit/action_list_all.csv")
refs_path = Path("docs/audit/action_references.csv")
out_path = Path("docs/audit/action_verdict_candidates.csv")

def load_actions(path):
    data = {}
    if not path.exists():
        return data
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            xmlid = row.get("xmlid") or ""
            if not xmlid:
                continue
            data[xmlid] = row
    return data

def load_refs(path):
    refs = {}
    if not path.exists():
        return refs
    with path.open(newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            xmlid = row.get("action_xmlid") or ""
            if not xmlid:
                continue
            refs.setdefault(xmlid, []).append(row)
    return refs

actions = load_actions(all_actions_path)
refs = load_refs(refs_path)

config_patterns = re.compile(r"^(ir\.|res\.|base\.|mail\.)|(?:setting|config|category|type|template|rule|access|group)", re.I)
cross_patterns = re.compile(r"^(project\.boq|project\.cost|project\.budget|project\.progress|construction\.contract|project\.material|purchase\.|stock\.|account\.|payment\.|settlement\.|sc\.settlement|sc\.payment)", re.I)

with out_path.open("w", newline="") as fh:
    writer = csv.writer(fh)
    writer.writerow(["role", "action_xmlid", "signals", "confidence", "suggested_verdict", "role_scope", "risk"])
    for xmlid, row in sorted(actions.items()):
        res_model = (row.get("res_model") or "").strip()
        view_mode = (row.get("view_mode") or "").strip()
        has_groups = (row.get("groups") or "").strip() != ""
        action_refs = refs.get(xmlid, [])
        has_refs = bool(action_refs)

        signals = []
        risk = []
        confidence = "low"
        verdict = "keep"

        if (not has_groups) and has_refs:
            signals.append("R01")
            risk.append("access_error_risk")
            confidence = "high"
            verdict = "degrade"

        if res_model and config_patterns.search(res_model):
            signals.append("R02")
            risk.append("config_risk")
            confidence = "high"
            verdict = "hide"

        if res_model and cross_patterns.search(res_model):
            signals.append("R03")
            risk.append("cross_domain_risk")
            if verdict != "hide":
                verdict = "degrade"
            if confidence == "low":
                confidence = "medium"

        if view_mode and any(x in view_mode for x in ["pivot", "graph"]):
            signals.append("R04")
            if confidence == "low":
                confidence = "low"
            if verdict == "keep":
                verdict = "degrade"

        if any("project_views.xml" in (r.get("ref_source") or "") for r in action_refs):
            signals.append("R05")
            if confidence == "medium":
                confidence = "high"
            if "access_error_risk" in risk:
                confidence = "high"

        if signals:
            writer.writerow([
                "demo_pm",
                xmlid,
                "|".join(signals),
                confidence,
                verdict,
                "pm_only",
                "|".join(sorted(set(risk))),
            ])
PY

echo "[audit.project.actions] wrote ${OUT_ACTIONS_MISSING}"
echo "[audit.project.actions] wrote ${OUT_ACTIONS_ALL}"
echo "[audit.project.actions] wrote ${OUT_ACTION_VIS}"
echo "[audit.project.actions] wrote ${OUT_ACTION_REFS}"
echo "[audit.project.actions] wrote ${OUT_ACTION_VERDICTS}"
