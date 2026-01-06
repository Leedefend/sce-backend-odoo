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

# ---------- Outputs (host) ----------
OUT_ACTIONS_ALL="${OUT_ACTIONS_ALL:-${OUT_DIR}/action_list_all.csv}"
OUT_ACTIONS_MISSING="${OUT_ACTIONS_MISSING:-${OUT_DIR}/action_groups_missing_db.csv}"
OUT_ACTION_VIS="${OUT_ACTION_VIS:-${OUT_DIR}/action_visibility_by_role.csv}"
OUT_ACTION_REFS="${OUT_ACTION_REFS:-${OUT_DIR}/action_references.csv}"
OUT_ACTION_VERDICTS="${OUT_ACTION_VERDICTS:-${OUT_DIR}/action_verdict_candidates.csv}"

OUT_VIEW_REFS="${OUT_VIEW_REFS:-${OUT_DIR}/action_view_refs.csv}"

OUT_OBJECT_VIS="${OUT_OBJECT_VIS:-${OUT_DIR}/object_button_visibility_by_role.csv}"
OUT_OBJECT_VERDICTS="${OUT_OBJECT_VERDICTS:-${OUT_DIR}/object_verdict_candidates.csv}"

# ---------- Runtime ----------
ODOO_ADDONS_PATH="${ODOO_ADDONS_PATH:-/usr/lib/python3/dist-packages/odoo/addons,/mnt/extra-addons,/mnt/addons_external/oca_server_ux}"
DB_PASSWORD="${DB_PASSWORD:-${DB_USER}}"

# ---------- Temp files (container) ----------
TMP_ACTIONS="${TMP_ACTIONS:-/tmp/sc_audit_project_actions.csv}"
TMP_VIS="${TMP_VIS:-/tmp/sc_audit_action_visibility.csv}"
TMP_MISSING="${TMP_MISSING:-/tmp/sc_audit_action_missing.csv}"
TMP_MENU_REFS="${TMP_MENU_REFS:-/tmp/sc_audit_action_menu_refs.csv}"
TMP_VIEW_REFS="${TMP_VIEW_REFS:-/tmp/sc_audit_action_view_refs.csv}"
TMP_OBJECT_VIS="${TMP_OBJECT_VIS:-/tmp/sc_audit_object_button_visibility.csv}"

# ---------- Host temp ----------
HOST_MENU_REFS="${HOST_MENU_REFS:-/tmp/sc_audit_action_menu_refs_host.csv}"
HOST_VIEW_REFS="${HOST_VIEW_REFS:-/tmp/sc_audit_action_view_refs_host.csv}"

# ---------- Feature toggles ----------
# enable heuristic suggestion CSVs (default off to keep audit pure)
ENABLE_SUGGESTIONS="${ENABLE_SUGGESTIONS:-0}"

mkdir -p "$OUT_DIR"

# =========================================================
# 1) Run evidence collection inside Odoo (container)
# =========================================================
compose_dev exec -T \
  -e TMP_ACTIONS="$TMP_ACTIONS" \
  -e TMP_VIS="$TMP_VIS" \
  -e TMP_MISSING="$TMP_MISSING" \
  -e TMP_MENU_REFS="$TMP_MENU_REFS" \
  -e TMP_VIEW_REFS="$TMP_VIEW_REFS" \
  -e TMP_OBJECT_VIS="$TMP_OBJECT_VIS" \
  odoo odoo shell -d "$DB_NAME" \
  --db_host=db --db_port=5432 --db_user="$DB_USER" --db_password="$DB_PASSWORD" \
  --addons-path="$ODOO_ADDONS_PATH" \
  --logfile=/dev/null --log-level=warn \
<<'PY'
import csv
import os
from lxml import etree

# ---------------- helpers ----------------
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

def user_groups_by_login(login):
    user = env["res.users"].sudo().with_context(active_test=False).search([("login", "=", login)], limit=1)
    if not user:
        return None, set(), []
    groups = user.groups_id.sudo()
    return user, set(groups.ids), group_xmlids(groups)

def parse_action_xmlid_from_node(node_name):
    # supports %(module.xmlid)d and ir.actions.act_window,<id>
    if not node_name:
        return ""
    name = node_name.strip()
    if name.startswith("%(") and name.endswith(")d"):
        return name[2:-2]
    if name.startswith("ir.actions.act_window,"):
        try:
            action_id = int(name.split(",", 1)[1])
        except Exception:
            return ""
        act = env["ir.actions.act_window"].sudo().browse(action_id)
        return xmlid_for(act) if act.exists() else ""
    return ""

# ---------------- collect actions ----------------
ProjectModel = env["ir.model"].sudo().search([("model", "=", "project.project")], limit=1)
action_ids = set()
act_servers = env["ir.actions.server"].sudo().browse([])

if ProjectModel:
    bound_windows = env["ir.actions.act_window"].sudo().search([("binding_model_id", "=", ProjectModel.id)])
    action_ids.update(bound_windows.ids)
    act_servers = env["ir.actions.server"].sudo().search([("binding_model_id", "=", ProjectModel.id)])

# menu reachable actions (act_window)
menus = env["ir.ui.menu"].sudo().search([("action", "!=", False)])
for m in menus:
    action_ref = m.action
    if not action_ref:
        continue
    if isinstance(action_ref, str):
        if not action_ref.startswith("ir.actions.act_window,"):
            continue
        try:
            action_ids.add(int(action_ref.split(",")[1]))
        except Exception:
            continue
    else:
        if getattr(action_ref, "_name", "") == "ir.actions.act_window":
            action_ids.add(action_ref.id)

act_windows = env["ir.actions.act_window"].sudo().browse(list(action_ids))

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
        "has_groups": bool(groups),
    })

tmp_actions = os.environ.get("TMP_ACTIONS", "/tmp/sc_audit_project_actions.csv")
with open(tmp_actions, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["action_type","action_id","xmlid","name","res_model","view_mode","binding_type","has_groups","groups"])
    for a in actions:
        w.writerow([
            a["action_type"], a["id"], a["xmlid"], a["name"], a["res_model"], a["view_mode"],
            a["binding_type"], "1" if a["has_groups"] else "0", ";".join(a["groups"])
        ])

# ---------------- role visibility for actions ----------------
roles = ["demo_pm", "demo_cost", "demo_readonly", "admin"]
role_groups = {}
for r in roles:
    user, ids, xmlids = user_groups_by_login(r)
    role_groups[r] = {"user_found": bool(user), "ids": ids, "xmlids": xmlids}

tmp_vis = os.environ.get("TMP_VIS", "/tmp/sc_audit_action_visibility.csv")
with open(tmp_vis, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["role","action_xmlid","action_name","res_model","view_mode","has_groups","groups_xmlids","visible"])
    for r in roles:
        r_meta = role_groups.get(r, {})
        r_ids = r_meta.get("ids", set())
        user_found = r_meta.get("user_found", False)
        for a in actions:
            visible = False
            if user_found:
                if not a["has_groups"]:
                    visible = True
                else:
                    visible = bool(set(r_ids) & set(a.get("group_ids", set())))
            w.writerow([r, a["xmlid"], a["name"], a["res_model"], a["view_mode"],
                        "1" if a["has_groups"] else "0", ";".join(a["groups"]), "1" if visible else "0"])

# ---------------- actions missing groups (raw) ----------------
tmp_missing = os.environ.get("TMP_MISSING", "/tmp/sc_audit_action_missing.csv")
with open(tmp_missing, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["action_type","xmlid","name","res_model","view_mode","binding_type","groups"])
    for a in actions:
        if a["has_groups"]:
            continue
        w.writerow([a["action_type"], a["xmlid"], a["name"], a["res_model"], a["view_mode"], a["binding_type"], ";".join(a["groups"])])

# ---------------- refs schema ----------------
ref_fields = [
    "action_xmlid","ref_type","ref_name","ref_xmlid","ref_source",
    "view_id","view_name","view_model","button_name_raw","button_type","groups_raw",
]

# ---------------- menu refs ----------------
tmp_menu_refs = os.environ.get("TMP_MENU_REFS", "/tmp/sc_audit_action_menu_refs.csv")
with open(tmp_menu_refs, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(ref_fields)
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
        if not action_xmlid and action_id:
            act = env["ir.actions.act_window"].sudo().browse(action_id)
            if act.exists():
                action_xmlid = xmlid_for(act)
        if not action_xmlid:
            continue

        w.writerow([action_xmlid,"menu",m.name or "", xmlid_for(m), action_source,"","","","","",""])

# ---------------- view refs + object buttons base list ----------------
tmp_view_refs = os.environ.get("TMP_VIEW_REFS", "/tmp/sc_audit_action_view_refs.csv")
tmp_object_vis = os.environ.get("TMP_OBJECT_VIS", "/tmp/sc_audit_object_button_visibility.csv")

object_buttons = []
with open(tmp_view_refs, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(ref_fields)
    views = env["ir.ui.view"].sudo().search([("model", "=", "project.project")])
    for v in views:
        arch = v.arch_db or ""
        try:
            root = etree.fromstring(arch.encode("utf-8"))
        except Exception:
            continue
        for node in root.xpath(".//*[@type='action' or @type='object']"):
            node_name = node.get("name") or ""
            if not node_name:
                continue
            button_type = (node.get("type") or "").strip()
            groups_raw = node.get("groups") or ""
            ref_name = node.get("string") or ""
            view_xmlid = xmlid_for(v)
            ref_source = f"{view_xmlid or v.id}:{v.type or ''}:{node_name}"

            action_xmlid = ""
            if button_type == "action":
                action_xmlid = parse_action_xmlid_from_node(node_name)
                if not action_xmlid:
                    continue

            if (v.type or "") == "kanban":
                ref_type = "kanban_action" if button_type == "action" else "kanban_object"
            else:
                ref_type = "view_button" if button_type == "action" else "view_object_button"

            w.writerow([
                action_xmlid, ref_type, ref_name, view_xmlid, ref_source,
                str(v.id), v.name or "", v.model or "", node_name, button_type, groups_raw
            ])

            if button_type == "object":
                object_buttons.append({
                    "ref_type": ref_type,
                    "ref_name": ref_name,
                    "ref_xmlid": view_xmlid,
                    "ref_source": ref_source,
                    "view_id": int(v.id),
                    "view_name": v.name or "",
                    "view_model": v.model or "project.project",
                    "view_type": v.type or "form",
                    "button_name_raw": node_name,
                    "groups_raw": groups_raw,
                })

# ---------------- final merged arch visibility for object buttons ----------------
view_arch_cache = {}
def get_final_arch_for_user(model, view_id, view_type, user):
    key = (user.id, model, view_id, view_type)
    if key in view_arch_cache:
        return view_arch_cache[key]
    arch = ""
    try:
        model_env = env[model].with_user(user)
        if hasattr(model_env, "get_view"):
            res = model_env.get_view(view_id=view_id, view_type=view_type, toolbar=False, submenu=False)
            arch = res.get("arch", "") if isinstance(res, dict) else (res or "")
        else:
            res = model_env.fields_view_get(view_id=view_id, view_type=view_type, toolbar=False, submenu=False)
            arch = res.get("arch", "")
    except Exception:
        arch = ""
    view_arch_cache[key] = arch
    return arch

def object_button_exists_in_arch(arch, button_name):
    if not arch or not button_name:
        return False
    try:
        root = etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return False
    nodes = root.xpath(f"//*[@name='{button_name}' and (not(@type) or @type='object')]")
    return bool(nodes)

with open(tmp_object_vis, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow([
        "role","ref_type","ref_name","ref_xmlid","ref_source",
        "view_id","view_name","view_model","button_name_raw","groups_raw","visible",
    ])
    for r in roles:
        user, _, _ = user_groups_by_login(r)
        user_found = bool(user)
        for ob in object_buttons:
            visible = False
            if user_found:
                arch = get_final_arch_for_user(ob["view_model"], ob["view_id"], ob["view_type"], user)
                visible = object_button_exists_in_arch(arch, ob["button_name_raw"])
            w.writerow([
                r, ob["ref_type"], ob["ref_name"], ob["ref_xmlid"], ob["ref_source"],
                str(ob["view_id"]), ob["view_name"], ob["view_model"], ob["button_name_raw"], ob["groups_raw"],
                "1" if visible else "0"
            ])
PY

# =========================================================
# 2) Export container temps -> host outputs
# =========================================================
compose_dev exec -T odoo cat "$TMP_MISSING"     >"$OUT_ACTIONS_MISSING"
compose_dev exec -T odoo cat "$TMP_ACTIONS"     >"$OUT_ACTIONS_ALL"
compose_dev exec -T odoo cat "$TMP_VIS"         >"$OUT_ACTION_VIS"
compose_dev exec -T odoo cat "$TMP_MENU_REFS"   >"$HOST_MENU_REFS"
compose_dev exec -T odoo cat "$TMP_VIEW_REFS"   >"$HOST_VIEW_REFS"
compose_dev exec -T odoo cat "$TMP_OBJECT_VIS"  >"$OUT_OBJECT_VIS"

# stable persisted files in OUT_DIR
cp -f "$HOST_VIEW_REFS" "$OUT_VIEW_REFS"

# =========================================================
# 3) Build action_references.csv (menu refs + view refs)
# =========================================================
{
  head -n 1 "$HOST_MENU_REFS" 2>/dev/null || echo "action_xmlid,ref_type,ref_name,ref_xmlid,ref_source,view_id,view_name,view_model,button_name_raw,button_type,groups_raw"
  tail -n +2 "$HOST_MENU_REFS" 2>/dev/null || true
  tail -n +2 "$HOST_VIEW_REFS" 2>/dev/null || true
} >"$OUT_ACTION_REFS"

# =========================================================
# 4) Optional: generate heuristic verdict candidates (OFF by default)
# =========================================================
if [ "$ENABLE_SUGGESTIONS" = "1" ]; then
  python3 - <<'PY'
import csv
import re
from pathlib import Path

all_actions_path = Path("docs/audit/action_list_all.csv")
refs_path = Path("docs/audit/action_references.csv")
out_path = Path("docs/audit/action_verdict_candidates.csv")

def load_actions(path: Path):
    data = {}
    if not path.exists():
        return data
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            xmlid = (row.get("xmlid") or "").strip()
            if xmlid:
                data[xmlid] = row
    return data

def load_refs(path: Path):
    refs = {}
    if not path.exists():
        return refs
    with path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            xmlid = (row.get("action_xmlid") or "").strip()
            if xmlid:
                refs.setdefault(xmlid, []).append(row)
    return refs

actions = load_actions(all_actions_path)
refs = load_refs(refs_path)

config_patterns = re.compile(r"^(ir\.|res\.|base\.|mail\.)|(?:setting|config|category|type|template|rule|access|group)", re.I)
cross_patterns = re.compile(r"^(project\.boq|project\.cost|project\.budget|project\.progress|construction\.contract|project\.material|purchase\.|stock\.|account\.|payment\.|settlement\.|sc\.settlement|sc\.payment)", re.I)

with out_path.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["role","action_xmlid","signals","confidence","suggested_verdict","role_scope","risk"])
    for xmlid, row in sorted(actions.items()):
        res_model = (row.get("res_model") or "").strip()
        view_mode = (row.get("view_mode") or "").strip()
        has_groups = (row.get("groups") or "").strip() != ""
        has_refs = bool(refs.get(xmlid))

        signals, risk = [], []
        confidence, verdict = "low", "keep"

        if (not has_groups) and has_refs:
            signals.append("R01"); risk.append("access_error_risk")
            confidence = "high"; verdict = "degrade"

        if res_model and config_patterns.search(res_model):
            signals.append("R02"); risk.append("config_risk")
            confidence = "high"; verdict = "hide"

        if res_model and cross_patterns.search(res_model):
            signals.append("R03"); risk.append("cross_domain_risk")
            if verdict != "hide": verdict = "degrade"
            if confidence == "low": confidence = "medium"

        if view_mode and any(x in view_mode for x in ["pivot","graph"]):
            signals.append("R04")
            if verdict == "keep": verdict = "degrade"

        if signals:
            w.writerow(["demo_pm", xmlid, "|".join(signals), confidence, verdict, "pm_only", "|".join(sorted(set(risk)))])
PY

  python3 - <<'PY'
import csv
import re
from pathlib import Path

object_vis_path = Path("docs/audit/object_button_visibility_by_role.csv")
object_out_path = Path("docs/audit/object_verdict_candidates.csv")

def load_rows(path: Path):
    if not path.exists():
        return []
    with path.open(newline="") as fh:
        return [r for r in csv.DictReader(fh) if (r.get("ref_type") or "") in {"view_object_button","kanban_object"}]

rows = load_rows(object_vis_path)

method_risk = re.compile(r"(import|rebuild|validate|generate|wizard|create|unlink|write|approve|post|confirm)", re.I)
cross_hint = re.compile(r"(boq|cost|budget|ledger|progress|contract|settlement|finance|payment|material|purchase)", re.I)

with object_out_path.open("w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["role","ref_type","ref_name","view_xmlid","view_id","view_model","button_name_raw","groups_raw","signals","confidence","suggested_verdict","role_scope","risk","ref_source"])
    for r in rows:
        role = r.get("role","")
        btn = r.get("button_name_raw","")
        ref_name = r.get("ref_name","")
        groups_raw = r.get("groups_raw","")

        signals, risk = [], []
        confidence, verdict = "low", "keep"

        if method_risk.search(btn):
            signals.append("O01"); risk.append("access_error_risk")
            confidence = "high"; verdict = "hide_for_pm"

        if not groups_raw or "_read" in groups_raw:
            signals.append("O02"); risk.append("access_error_risk")
            if confidence != "high": confidence = "medium"
            if verdict == "keep": verdict = "review_groups"

        if cross_hint.search(btn) or cross_hint.search(ref_name):
            signals.append("O03"); risk.append("cross_domain_risk")
            if confidence == "low": confidence = "medium"
            if verdict == "keep": verdict = "degrade_or_hide"

        if (r.get("ref_type") or "") == "kanban_object":
            signals.append("O04"); risk.append("high_frequency_risk")
            if confidence == "low": confidence = "medium"

        w.writerow([
            role,
            r.get("ref_type",""),
            ref_name,
            r.get("ref_xmlid",""),
            r.get("view_id",""),
            r.get("view_model",""),
            btn,
            groups_raw,
            "|".join(signals),
            confidence,
            verdict,
            "pm_only",
            "|".join(sorted(set(risk))),
            r.get("ref_source",""),
        ])
PY
fi

echo "[audit.project.actions] wrote ${OUT_ACTIONS_MISSING}"
echo "[audit.project.actions] wrote ${OUT_ACTIONS_ALL}"
echo "[audit.project.actions] wrote ${OUT_ACTION_VIS}"
echo "[audit.project.actions] wrote ${OUT_VIEW_REFS}"
echo "[audit.project.actions] wrote ${OUT_ACTION_REFS}"
echo "[audit.project.actions] wrote ${OUT_OBJECT_VIS}"
if [ "$ENABLE_SUGGESTIONS" = "1" ]; then
  echo "[audit.project.actions] wrote ${OUT_ACTION_VERDICTS}"
  echo "[audit.project.actions] wrote ${OUT_OBJECT_VERDICTS}"
else
  echo "[audit.project.actions] suggestions disabled (set ENABLE_SUGGESTIONS=1 to generate verdict candidates)"
fi
