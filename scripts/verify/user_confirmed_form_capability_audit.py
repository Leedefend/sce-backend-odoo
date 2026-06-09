# -*- coding: utf-8 -*-
"""Audit form capability for user-confirmed formal menu entries.

Run inside Odoo shell:
    odoo shell -d sc_demo < scripts/verify/user_confirmed_form_capability_audit.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

from odoo.addons.smart_construction_core.models.support.p1_daily_business_visible_alias_fields import (
    MODEL_LABEL_SOURCE_OVERRIDES,
    P1_ALIAS_COMPAT_LABELS,
    P1_ALIAS_LABELS,
    _alias_field_name,
)


BASELINE_CANDIDATES = (
    Path("/mnt/scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json"),
    Path("scripts/verify/baselines/user_confirmed_formal_menu_policy_62.json"),
)
OUTPUT_DIR_CANDIDATES = (
    Path("/mnt/docs/audit/user_confirmed_form_capability"),
    Path("docs/audit/user_confirmed_form_capability"),
    Path("/tmp/user_confirmed_form_capability"),
)
PRODUCT_KEY = "construction.standard"

P1_ALIAS_FIELD_LABELS = {
    model_name: {
        _alias_field_name(label): label
        for label in list(dict.fromkeys(list(labels) + P1_ALIAS_COMPAT_LABELS.get(model_name, [])))
    }
    for model_name, labels in P1_ALIAS_LABELS.items()
}


def _strip_ns(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _parse_arch(arch):
    if not arch:
        return None
    try:
        return ET.fromstring(arch.encode("utf-8"))
    except Exception:
        return None


def _iter_nodes(root):
    if root is None:
        return []
    return list(root.iter())


def _node_bool_disabled(node, name):
    value = (node.get(name) or "").strip().lower()
    return value in {"0", "false"}


def _field_names(root):
    return {
        node.get("name")
        for node in _iter_nodes(root)
        if _strip_ns(node.tag) == "field" and node.get("name")
    }


def _field_labels(root):
    labels = {}
    for node in _iter_nodes(root):
        if _strip_ns(node.tag) != "field" or not node.get("name"):
            continue
        labels[node.get("name")] = node.get("string") or ""
    return labels


def _formal_equivalent_fields(model_name, alias_field, model_fields):
    label = P1_ALIAS_FIELD_LABELS.get(model_name, {}).get(alias_field)
    if not label:
        return set()
    candidates = set(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label) or [])
    for field_name, field in model_fields.items():
        if field_name.startswith("p1_visible_"):
            continue
        if field.string == label:
            candidates.add(field_name)
    return {field_name for field_name in candidates if field_name in model_fields}


def _label_equivalent_fields(model_name, label, model_fields):
    if not label:
        return set()
    candidates = set(MODEL_LABEL_SOURCE_OVERRIDES.get(model_name, {}).get(label) or [])
    if model_name == "project.project" and label == "关联单位":
        candidates.add("partner_id")
    for candidate_name, field in model_fields.items():
        if candidate_name.startswith(("legacy_visible_", "accepted_visible_", "p1_visible_", "user_acceptance_")):
            continue
        if field.string == label:
            candidates.add(candidate_name)
    return {candidate_name for candidate_name in candidates if candidate_name in model_fields}


def _field_is_represented_on_form(model_name, field_name, form_fields, model_fields, label=""):
    if field_name in form_fields:
        return True
    if field_name.startswith("p1_visible_"):
        return bool(_formal_equivalent_fields(model_name, field_name, model_fields) & form_fields)
    if field_name.startswith(("legacy_visible_", "accepted_visible_", "user_acceptance_")):
        return bool(_label_equivalent_fields(model_name, label, model_fields) & form_fields)
    return bool(label and _label_equivalent_fields(model_name, label, model_fields) & form_fields)


def _button_names(root):
    return [
        node.get("name")
        for node in _iter_nodes(root)
        if _strip_ns(node.tag) == "button" and node.get("name")
    ]


def _statusbar_fields(root):
    return [
        node.get("name")
        for node in _iter_nodes(root)
        if _strip_ns(node.tag) == "field" and node.get("widget") == "statusbar" and node.get("name")
    ]


def _load_baseline():
    for path in BASELINE_CANDIDATES:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8")), path
    raise FileNotFoundError("missing user_confirmed_formal_menu_policy_62.json")


def _output_dir():
    for path in OUTPUT_DIR_CANDIDATES:
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / ".write_probe"
            probe.write_text("", encoding="utf-8")
            probe.unlink()
            return path
        except OSError:
            continue
    raise OSError("cannot create audit output directory")


def _menus_for_product(baseline):
    for product in baseline.get("products") or []:
        if product.get("product_key") != PRODUCT_KEY:
            continue
        menus = []
        for group in product.get("menu_groups") or []:
            for menu in group.get("menus") or []:
                if menu.get("enabled", True):
                    row = dict(menu)
                    row["group_label"] = group.get("label") or group.get("group_label") or ""
                    menus.append(row)
        return menus
    return []


def _action_view_id(action_read, view_type):
    for view_id, mode in action_read.get("views") or []:
        if mode == view_type and view_id:
            return int(view_id)
    return False


def _view_arch(model_name, view_type, view_id=False):
    Model = env[model_name].sudo()  # noqa: F821
    try:
        data = Model.get_view(view_id=view_id or None, view_type=view_type)
    except AttributeError:
        data = Model.fields_view_get(view_id=view_id or None, view_type=view_type, toolbar=False)
    return data.get("arch") or data.get("arch_db") or ""


def _business_methods(model_name):
    Model = env[model_name]  # noqa: F821
    names = []
    for name in dir(Model):
        if name.startswith("action_") and not name.startswith("action_open_") and not name.startswith("action_view_"):
            names.append(name)
    return sorted(set(names))


def _model_has_write_access(model_name):
    try:
        return bool(env[model_name].check_access_rights("write", raise_exception=False))  # noqa: F821
    except Exception:
        return False


def _resolve_action(menu):
    action_id = int(menu.get("action_id") or 0)
    Action = env["ir.actions.act_window"].sudo()  # noqa: F821
    action = Action.browse(action_id)
    if action.exists():
        return action, action_id
    menu_xmlid = menu.get("menu_xmlid") or menu.get("menu_key") or menu.get("page_key") or ""
    current_menu = env.ref(menu_xmlid, raise_if_not_found=False) if menu_xmlid else False  # noqa: F821
    if current_menu and current_menu.action and current_menu.action._name == "ir.actions.act_window":
        return current_menu.action.sudo(), current_menu.action.id
    return action, action_id


def _audit_menu(menu):
    action, action_id = _resolve_action(menu)
    row = {
        "group": menu.get("group_label") or "",
        "menu": menu.get("label") or menu.get("name") or "",
        "menu_xmlid": menu.get("menu_xmlid") or "",
        "action_id": action_id,
        "action_exists": bool(action.exists()),
        "action_name": "",
        "model": menu.get("res_model") or "",
        "view_mode": ",".join(menu.get("view_modes") or []),
        "form_mode": False,
        "form_arch": False,
        "form_create_enabled": False,
        "form_edit_enabled": False,
        "form_fields": 0,
        "list_fields": 0,
        "list_fields_missing_on_form": [],
        "has_state_field": False,
        "has_statusbar": False,
        "statusbar_fields": [],
        "business_methods": [],
        "form_buttons": [],
        "business_methods_missing_buttons": [],
        "write_access_for_current_user": False,
        "gaps": [],
        "severity": "ok",
    }
    if not action.exists():
        row["gaps"].append("missing_action")
        row["severity"] = "blocker"
        return row

    action_data = action.read(["name", "res_model", "view_mode", "views"])[0]
    model_name = action_data.get("res_model") or row["model"]
    row["action_name"] = action_data.get("name") or ""
    row["model"] = model_name
    row["view_mode"] = action_data.get("view_mode") or row["view_mode"]
    row["form_mode"] = "form" in {item.strip() for item in (row["view_mode"] or "").split(",")}
    row["write_access_for_current_user"] = _model_has_write_access(model_name)

    if not row["form_mode"]:
        row["gaps"].append("action_without_form_mode")
        row["severity"] = "blocker"
        return row

    form_arch = _view_arch(model_name, "form", _action_view_id(action_data, "form"))
    form_root = _parse_arch(form_arch)
    row["form_arch"] = form_root is not None
    if form_root is None:
        row["gaps"].append("missing_or_invalid_form_arch")
        row["severity"] = "blocker"
        return row

    form_fields = _field_names(form_root)
    form_buttons = _button_names(form_root)
    statusbar_fields = _statusbar_fields(form_root)
    root_tag = _strip_ns(form_root.tag)
    row["form_create_enabled"] = root_tag == "form" and not _node_bool_disabled(form_root, "create")
    row["form_edit_enabled"] = root_tag == "form" and not _node_bool_disabled(form_root, "edit")
    row["form_fields"] = len(form_fields)
    row["form_buttons"] = form_buttons
    row["statusbar_fields"] = statusbar_fields
    row["has_statusbar"] = bool(statusbar_fields)

    model_fields = env[model_name]._fields  # noqa: F821
    row["has_state_field"] = "state" in model_fields
    if row["has_state_field"] and "state" not in form_fields:
        row["gaps"].append("state_field_missing_on_form")
    if row["has_state_field"] and not statusbar_fields:
        row["gaps"].append("state_statusbar_missing")

    business_methods = _business_methods(model_name)
    row["business_methods"] = business_methods
    missing_buttons = [
        name for name in business_methods
        if name not in set(form_buttons) and name not in {"action_create_payment_execution"}
    ]
    row["business_methods_missing_buttons"] = missing_buttons
    if row["has_state_field"] and business_methods and not form_buttons:
        row["gaps"].append("stateful_business_model_without_form_buttons")

    try:
        list_arch = _view_arch(model_name, "tree", _action_view_id(action_data, "tree"))
    except Exception:
        list_arch = ""
    list_root = _parse_arch(list_arch)
    list_fields = _field_names(list_root)
    list_labels = _field_labels(list_root)
    row["list_fields"] = len(list_fields)
    missing_list_fields = sorted(
        field for field in list_fields
        if field in model_fields
        and field not in {"create_date", "create_uid", "write_date", "write_uid"}
        and not field.endswith("_count")
        and not _field_is_represented_on_form(model_name, field, form_fields, model_fields, list_labels.get(field) or "")
    )
    row["list_fields_missing_on_form"] = missing_list_fields[:30]
    if missing_list_fields:
        row["gaps"].append("list_fields_missing_on_form")

    if row["gaps"] and row["severity"] == "ok":
        row["severity"] = "needs_review"
    return row


def _write_markdown(path, rows, summary):
    lines = [
        "# 用户确认菜单表单能力审计",
        "",
        f"- 产品：`{PRODUCT_KEY}`",
        f"- 菜单数：{summary['menus']}",
        f"- 阻断项：{summary['severity_counts'].get('blocker', 0)}",
        f"- 需复核：{summary['severity_counts'].get('needs_review', 0)}",
        f"- 通过：{summary['severity_counts'].get('ok', 0)}",
        "",
        "| 分组 | 菜单 | 模型 | 严重度 | 缺口 | 列表字段未进表单 | 表单按钮 |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        gaps = ", ".join(row["gaps"]) or "-"
        missing = ", ".join(row["list_fields_missing_on_form"][:8]) or "-"
        buttons = ", ".join(row["form_buttons"][:8]) or "-"
        lines.append(
            "| {group} | {menu} | `{model}` | {severity} | {gaps} | {missing} | {buttons} |".format(
                group=row["group"],
                menu=row["menu"],
                model=row["model"],
                severity=row["severity"],
                gaps=gaps,
                missing=missing,
                buttons=buttons,
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


baseline, baseline_path = _load_baseline()
menus = _menus_for_product(baseline)
rows = [_audit_menu(menu) for menu in menus]
severity_counts = Counter(row["severity"] for row in rows)
gap_counts = Counter(gap for row in rows for gap in row["gaps"])
model_counts = Counter(row["model"] for row in rows)
summary = {
    "audit": "user_confirmed_form_capability_audit",
    "baseline": str(baseline_path),
    "product_key": PRODUCT_KEY,
    "menus": len(rows),
    "models": len(model_counts),
    "severity_counts": dict(severity_counts),
    "gap_counts": dict(gap_counts),
    "top_reused_models": model_counts.most_common(10),
    "status": "PASS" if not severity_counts.get("blocker") else "FAIL",
}

out_dir = _output_dir()
(out_dir / "user_confirmed_form_capability_audit.json").write_text(
    json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
_write_markdown(out_dir / "user_confirmed_form_capability_audit.md", rows, summary)
print(json.dumps(summary, ensure_ascii=False))
