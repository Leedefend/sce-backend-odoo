#!/usr/bin/env python3
"""Audit visible business pages for English labels and technical field leakage."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from lxml import etree


TECHNICAL_FIELD_PATTERNS = (
    "legacy",
    "migration",
    "migrate",
    "source_origin",
    "source_table",
    "source_model",
    "source_id",
    "raw",
    "payload",
    "trace",
    "debug",
    "xmlid",
    "external",
)
TECHNICAL_LABEL_PATTERNS = (
    "历史",
    "迁移",
    "原始",
    "legacy",
    "migration",
    "source",
    "raw",
    "payload",
    "trace",
    "debug",
    "xmlid",
)
ENGLISH_WORD_RE = re.compile(r"[A-Za-z]{3,}")
DEFAULT_MENU_ROOTS = ("智能施工 2.0", "业务配置")


def artifact_root() -> Path:
    candidates = []
    env_root = os.getenv("MIGRATION_ARTIFACT_ROOT")
    if env_root:
        candidates.append(Path(env_root))
    candidates.append(Path("/mnt/artifacts/migration"))
    candidates.append(Path(f"/tmp/business_fact_page_surface_audit/{env.cr.dbname}"))  # noqa: F821
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


def menu_path(menu) -> str:
    names = []
    current = menu
    while current:
        names.append(current.name)
        current = current.parent_id
    return " / ".join(reversed(names))


def issue(kind, menu, action, view, field_name="", label=""):
    return {
        "kind": kind,
        "menu": menu,
        "action": action.name if action else "",
        "model": action.res_model if action else "",
        "view": view.xml_id or view.name if view else "",
        "field": field_name,
        "label": label,
    }


def is_technical_field(field_name: str) -> bool:
    lowered = field_name.lower()
    return any(pattern in lowered for pattern in TECHNICAL_FIELD_PATTERNS)


def is_technical_label(label: str) -> bool:
    lowered = label.lower()
    return any(pattern in lowered for pattern in TECHNICAL_LABEL_PATTERNS)


login = os.getenv("AUDIT_LOGIN", "wutao")
menu_roots = tuple(
    part.strip()
    for part in os.getenv("AUDIT_MENU_ROOTS", ",".join(DEFAULT_MENU_ROOTS)).split(",")
    if part.strip()
)
Users = env["res.users"].sudo().with_context(active_test=False)  # noqa: F821
Menu = env["ir.ui.menu"].sudo()  # noqa: F821
Views = env["ir.ui.view"].sudo()  # noqa: F821
user = Users.search([("login", "=", login)], limit=1)

rows = []
scanned_views = set()
scanned_actions = 0
visible_menu_count = 0
scoped_menu_count = 0

if user:
    visible_ids = Menu.with_user(user)._visible_menu_ids(debug=False)
    visible_menu_count = len(visible_ids)
    for menu in Menu.browse(visible_ids):
        path = menu_path(menu)
        if menu_roots and not any(path == root or path.startswith(root + " / ") for root in menu_roots):
            continue
        scoped_menu_count += 1
        action_ref = menu.action
        if not action_ref or action_ref._name != "ir.actions.act_window":
            continue
        action = action_ref.sudo()
        if not action.res_model or not action.res_model.startswith(("sc.", "project.", "hr.department")):
            continue
        scanned_actions += 1
        model = env[action.res_model].sudo()  # noqa: F821
        if ENGLISH_WORD_RE.search(action.name or ""):
            rows.append(issue("english_action_name", path, action, False, label=action.name))
        if ENGLISH_WORD_RE.search(model._description or ""):
            rows.append(issue("english_model_description", path, action, False, label=model._description))

        view_candidates = []
        for action_view in action.view_ids:
            if action_view.view_id:
                view_candidates.append(action_view.view_id)
        if action.view_id:
            view_candidates.append(action.view_id)
        for view_type in ("tree", "form", "search"):
            default_view = Views.search(
                [("model", "=", action.res_model), ("type", "=", view_type)],
                order="priority, id",
                limit=1,
            )
            if default_view:
                view_candidates.append(default_view)

        for view in view_candidates:
            if not view or view.id in scanned_views:
                continue
            scanned_views.add(view.id)
            try:
                root = etree.fromstring((view.arch_db or "").encode("utf-8"))
            except Exception:
                continue
            for node in root.xpath(".//*[@string]"):
                label = node.get("string") or ""
                if ENGLISH_WORD_RE.search(label):
                    rows.append(issue("english_view_label", path, action, view, label=label))
                if is_technical_label(label):
                    rows.append(issue("technical_view_label", path, action, view, label=label))
            for node in root.xpath(".//field[@name]"):
                field_name = node.get("name") or ""
                field = model._fields.get(field_name)
                if not field:
                    continue
                label = node.get("string") or field.string
                if is_technical_field(field_name):
                    rows.append(issue("technical_field_visible", path, action, view, field_name, label))
                if label:
                    if ENGLISH_WORD_RE.search(label):
                        rows.append(issue("english_field_label", path, action, view, field_name, label))
                    if is_technical_label(label):
                        rows.append(issue("technical_field_label", path, action, view, field_name, label))

payload = {
    "status": "PASS" if user else "FAIL",
    "decision": "business_page_surface_gap_present" if rows else "business_page_surface_ready",
    "database": env.cr.dbname,  # noqa: F821
    "login": login,
    "menu_roots": menu_roots,
    "user_exists": bool(user),
    "visible_menu_count": visible_menu_count,
    "scoped_menu_count": scoped_menu_count,
    "scanned_action_count": scanned_actions,
    "scanned_view_count": len(scanned_views),
    "issue_count": len(rows),
    "issue_summary": {},
    "menu_issue_summary": {},
    "issues": rows[:300],
}
summary = {}
menu_summary = {}
for row in rows:
    summary[row["kind"]] = summary.get(row["kind"], 0) + 1
    menu_summary[row["menu"]] = menu_summary.get(row["menu"], 0) + 1
payload["issue_summary"] = summary
payload["menu_issue_summary"] = dict(
    sorted(menu_summary.items(), key=lambda item: (-item[1], item[0]))[:50]
)

output = artifact_root() / "business_fact_page_surface_audit_probe_result_v1.json"
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("BUSINESS_FACT_PAGE_SURFACE_AUDIT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
if not user:
    raise RuntimeError({"business_fact_page_surface_audit": "missing user", "login": login})
