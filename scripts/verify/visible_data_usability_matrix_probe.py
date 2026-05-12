#!/usr/bin/env python3
"""Build a menu-driven visible data and usability matrix.

This script is intended to run inside ``odoo shell``.  It uses the current
user-visible menu/action facts as the source of truth, then checks whether each
business page has usable view structures, search controls, access rights, and
sample data coverage for fields that are visible in native views.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

from lxml import etree
from odoo.tools.safe_eval import safe_eval


DEFAULT_MENU_ROOTS = ("智慧施工管理平台", "项目", "业务配置")
DEFAULT_MODEL_PREFIXES = ("project.", "sc.", "construction.", "tender.", "payment.", "hr.department")
SKIP_FIELD_TYPES = {"binary", "html"}


def _artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("VISIBLE_MATRIX_ARTIFACT_ROOT") or os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/visible_data_usability_closure"))
    candidates.append(Path(f"/tmp/visible_data_usability_closure/{env.cr.dbname}"))  # noqa: F821
    for root in candidates:
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
            return root
        except Exception:
            continue
    raise RuntimeError({"artifact_root_unavailable": [str(path) for path in candidates]})


def _as_list(value):
    return value if isinstance(value, list) else []


def _norm(value) -> str:
    return str(value or "").strip()


def _menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return " / ".join(reversed(names))


def _safe_eval(value, fallback):
    if not value:
        return fallback
    if isinstance(value, (list, tuple, dict)):
        return value
    try:
        return safe_eval(str(value), {"uid": user.id, "user": user, "context": {}})  # noqa: F821
    except Exception:
        return fallback


def _view_candidates(action, view_type: str):
    Views = env["ir.ui.view"].sudo()  # noqa: F821
    out = []
    for action_view in action.view_ids:
        if action_view.view_mode == view_type and action_view.view_id:
            out.append(action_view.view_id)
    if action.view_id and action.view_id.type == view_type:
        out.append(action.view_id)
    default_view = Views.search(
        [("model", "=", action.res_model), ("type", "=", view_type)],
        order="priority, id",
        limit=1,
    )
    if default_view:
        out.append(default_view)
    seen = set()
    unique = []
    for view in out:
        if view.id not in seen:
            unique.append(view)
            seen.add(view.id)
    return unique


def _resolved_arch(model, view, view_type: str) -> str:
    try:
        data = model.get_view(view_id=view.id if view else False, view_type=view_type)
        arch = data.get("arch") if isinstance(data, dict) else ""
        if arch:
            return arch
    except Exception:
        pass
    return view.arch_db or "" if view else ""


def _parse_view(model, view, view_type: str):
    arch = _resolved_arch(model, view, view_type)
    try:
        return etree.fromstring(arch.encode("utf-8"))
    except Exception:
        return None


def _is_static_invisible_node(node) -> bool:
    raw_values = [
        node.get("invisible"),
        node.get("column_invisible"),
    ]
    for raw in raw_values:
        if _norm(raw).lower() in {"1", "true", "yes"}:
            return True
    modifiers = node.get("modifiers")
    if modifiers:
        try:
            data = json.loads(modifiers)
        except Exception:
            data = {}
        if data.get("invisible") is True or data.get("column_invisible") is True:
            return True
    return False


def _field_names_from_view(view, model):
    root = _parse_view(model, view, view.type if view else "")
    if root is None:
        return []
    names = []
    for node in root.xpath(".//field[@name]"):
        if _is_static_invisible_node(node):
            continue
        name = node.get("name")
        field = model._fields.get(name or "")
        if not field or field.type in SKIP_FIELD_TYPES:
            continue
        if name not in names:
            names.append(name)
    return names


def _search_controls(view, model):
    root = _parse_view(model, view, "search")
    if root is None:
        return {"filters": 0, "group_by": 0, "fields": 0}
    filters = 0
    group_by = 0
    for node in root.xpath(".//filter"):
        filters += 1
        context_raw = node.get("context") or ""
        if "group_by" in context_raw:
            group_by += 1
    return {
        "filters": filters,
        "group_by": group_by,
        "fields": len(root.xpath(".//field[@name]")),
    }


def _is_empty(value) -> bool:
    if value is False or value is None:
        return True
    if value in ("", [], ()):
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _sample_domain(action):
    domain = _safe_eval(action.domain, [])
    return domain if isinstance(domain, list) else []


def _field_completeness(model, records, field_names):
    rows = []
    if not records or not field_names:
        return rows
    read_fields = ["id"]
    for name in field_names:
        field = model._fields.get(name)
        if field and field.type not in SKIP_FIELD_TYPES:
            read_fields.append(name)
    read_fields = list(dict.fromkeys(read_fields))
    try:
        values = records.read(read_fields)
    except Exception:
        values = []
    total = len(values)
    for name in read_fields:
        if name == "id":
            continue
        field = model._fields.get(name)
        if not field:
            continue
        empty_count = sum(1 for row in values if _is_empty(row.get(name)))
        rows.append(
            {
                "field": name,
                "label": field.string,
                "type": field.type,
                "required": bool(field.required),
                "empty_count": empty_count,
                "sample_count": total,
                "empty_ratio": round(empty_count / total, 4) if total else 0,
            }
        )
    return rows


def _access_matrix(model):
    out = {}
    for mode in ("read", "create", "write", "unlink"):
        try:
            out[mode] = bool(model.check_access_rights(mode, raise_exception=False))
        except Exception:
            out[mode] = False
    return out


def _issue(kind, severity, row, detail=""):
    return {
        "kind": kind,
        "severity": severity,
        "menu": row["menu"],
        "action_id": row["action_id"],
        "model": row["model"],
        "detail": detail,
    }


login = os.getenv("AUDIT_LOGIN", "wutao")
menu_roots = tuple(
    part.strip()
    for part in os.getenv("AUDIT_MENU_ROOTS", ",".join(DEFAULT_MENU_ROOTS)).split(",")
    if part.strip()
)
model_prefixes = tuple(
    part.strip()
    for part in os.getenv("VISIBLE_MATRIX_MODEL_PREFIXES", ",".join(DEFAULT_MODEL_PREFIXES)).split(",")
    if part.strip()
)
limit_actions = int(os.getenv("VISIBLE_MATRIX_LIMIT_ACTIONS", "120"))
sample_limit = int(os.getenv("VISIBLE_MATRIX_SAMPLE_LIMIT", "20"))

Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
Menu = env["ir.ui.menu"].sudo()  # noqa: F821
user = Users.search([("login", "=", login)], limit=1)

visible_menu_count = 0
scoped_menu_count = 0
actions = []
if user:
    visible_ids = Menu.with_user(user)._visible_menu_ids(debug=False)
    visible_menu_count = len(visible_ids)
    for menu in Menu.browse(visible_ids):
        path = _menu_path(menu)
        if menu_roots and not any(path == root or path.startswith(root + " / ") for root in menu_roots):
            continue
        scoped_menu_count += 1
        action_ref = menu.action
        if not action_ref or action_ref._name != "ir.actions.act_window":
            continue
        action = action_ref.sudo()
        if not action.res_model or not action.view_mode:
            continue
        if model_prefixes and not action.res_model.startswith(model_prefixes):
            continue
        actions.append((path, menu, action))
        if len(actions) >= limit_actions:
            break

matrix = []
issues = []
summary_by_model = defaultdict(int)
summary_by_kind = defaultdict(int)

for path, menu, action in actions:
    model = env[action.res_model].with_user(user)  # noqa: F821
    view_modes = [_norm(mode) for mode in (action.view_mode or "").split(",") if _norm(mode)]
    native_view_types = {"tree" if mode == "list" else mode for mode in view_modes}
    view_fields = {}
    view_ids = {}
    search_controls = {"filters": 0, "group_by": 0, "fields": 0}
    for view_type in ("tree", "form", "kanban", "search"):
        candidates = _view_candidates(action, view_type)
        view = candidates[0] if candidates else False
        view_ids[view_type] = view.id if view else 0
        if view and view_type == "search":
            search_controls = _search_controls(view, model)
        elif view and view_type in {"tree", "form", "kanban"}:
            view_fields[view_type] = _field_names_from_view(view, model)
        else:
            view_fields[view_type] = []

    visible_field_names = []
    for names in view_fields.values():
        for name in names:
            if name not in visible_field_names:
                visible_field_names.append(name)

    access = _access_matrix(model)
    domain = _sample_domain(action)
    records = model.search(domain, limit=sample_limit) if access.get("read") else model.browse()
    try:
        record_count = model.search_count(domain) if access.get("read") else 0
    except Exception:
        record_count = len(records)
    completeness = _field_completeness(model, records, visible_field_names)
    required_empty = [
        row for row in completeness if row["required"] and row["sample_count"] and row["empty_count"] > 0
    ]
    high_empty = [
        row
        for row in completeness
        if not row["required"] and row["sample_count"] >= 5 and row["empty_ratio"] >= 0.8
    ][:12]

    row = {
        "menu_id": menu.id,
        "menu": path,
        "action_id": action.id,
        "action_name": action.name,
        "model": action.res_model,
        "model_label": model._description,
        "view_mode": action.view_mode,
        "native_view_types": sorted(native_view_types),
        "view_ids": view_ids,
        "view_field_counts": {key: len(value) for key, value in view_fields.items()},
        "search_controls": search_controls,
        "access": access,
        "record_count": record_count,
        "sample_count": len(records),
        "visible_field_count": len(visible_field_names),
        "required_empty": required_empty[:20],
        "high_empty": high_empty,
    }
    matrix.append(row)
    summary_by_model[action.res_model] += 1

    if "tree" in native_view_types and not view_fields["tree"]:
        issues.append(_issue("missing_list_structure", "error", row))
    if "form" in native_view_types and not view_fields["form"]:
        issues.append(_issue("missing_form_structure", "error", row))
    if "kanban" in native_view_types and not view_fields["kanban"]:
        issues.append(_issue("missing_kanban_structure", "warning", row))
    if not access.get("read"):
        issues.append(_issue("read_access_unavailable", "error", row))
    if record_count == 0 and not action.res_model.startswith(("project.project.stage", "project.tags")):
        issues.append(_issue("no_visible_records", "warning", row))
    if required_empty:
        issues.append(
            _issue(
                "required_visible_field_empty",
                "error",
                row,
                ",".join(item["field"] for item in required_empty[:8]),
            )
        )
    if high_empty:
        issues.append(
            _issue(
                "visible_field_high_empty_ratio",
                "warning",
                row,
                ",".join(item["field"] for item in high_empty[:8]),
            )
        )
    if "search" in native_view_types and not any(search_controls.values()):
        issues.append(_issue("missing_search_controls", "warning", row))

for item in issues:
    summary_by_kind[item["kind"]] += 1

payload = {
    "ok": bool(user) and scoped_menu_count > 0 and not any(item["severity"] == "error" for item in issues),
    "database": env.cr.dbname,  # noqa: F821
    "login": login,
    "menu_roots": menu_roots,
    "model_prefixes": model_prefixes,
    "visible_menu_count": visible_menu_count,
    "scoped_menu_count": scoped_menu_count,
    "scanned_action_count": len(matrix),
    "issue_count": len(issues),
    "error_count": sum(1 for item in issues if item["severity"] == "error"),
    "warning_count": sum(1 for item in issues if item["severity"] == "warning"),
    "issue_summary": dict(sorted(summary_by_kind.items())),
    "model_summary": dict(sorted(summary_by_model.items())),
    "issues": issues[:500],
    "matrix": matrix,
}

output = _artifact_root() / "visible_data_usability_matrix_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("VISIBLE_DATA_USABILITY_MATRIX=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))

if not user:
    raise RuntimeError({"visible_data_usability_matrix": "missing user", "login": login})
if scoped_menu_count <= 0:
    raise RuntimeError(
        {
            "visible_data_usability_matrix": "no scoped visible menus",
            "login": login,
            "menu_roots": menu_roots,
            "visible_menu_count": visible_menu_count,
        }
    )
