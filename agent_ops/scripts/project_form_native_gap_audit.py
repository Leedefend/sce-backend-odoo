#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VERIFY_DIR = ROOT / "scripts" / "verify"
if str(VERIFY_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFY_DIR))

from intent_smoke_utils import require_ok  # type: ignore
from python_http_smoke_utils import get_base_url, http_post_json  # type: ignore


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit native project form facts versus parsed contract facts")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--password", help="User password for live ui.contract fetch")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    return parser.parse_args()


def build_probe_code(db: str, login: str) -> str:
    return f"""
import json
import xml.etree.ElementTree as ET
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

config.parse_config(["-c", "/var/lib/odoo/odoo.conf", "-d", {db!r}])
registry = odoo.registry({db!r})


def walk_layout(nodes, type_counter, field_names):
    for node in (nodes or []):
        if not isinstance(node, dict):
            continue
        ntype = str(node.get("type") or "").strip()
        if ntype:
            type_counter[ntype] = type_counter.get(ntype, 0) + 1
        fname = str(node.get("name") or "").strip()
        if ntype == "field" and fname:
            field_names.add(fname)
        walk_layout(node.get("children") or [], type_counter, field_names)


def key_of(row):
    if not isinstance(row, dict):
        return ""
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {{}}
    return str(
        row.get("key")
        or row.get("label")
        or row.get("string")
        or row.get("name")
        or payload.get("method")
        or payload.get("ref")
        or ""
    ).strip()


with registry.cursor() as cr:
    su_env = api.Environment(cr, SUPERUSER_ID, {{}})
    user = su_env["res.users"].search([("login", "=", {login!r})], limit=1)
    if not user:
        raise SystemExit("user not found")

    owner = su_env["app.view.config"]
    view_data = owner._safe_get_view_data("project.project", "form") or {{}}
    arch = str(view_data.get("arch") or "").strip()
    fields_meta = view_data.get("fields") if isinstance(view_data.get("fields"), dict) else {{}}

    native = {{
        "root_tag": "",
        "header_buttons_count": 0,
        "header_buttons_labels": [],
        "button_box_count": 0,
        "button_box_labels": [],
        "notebook_count": 0,
        "page_count": 0,
        "page_labels": [],
        "group_count": 0,
        "field_node_count": 0,
        "field_names_count": 0,
        "field_names_sample": [],
        "statusbar_fields": [],
        "fields_meta_count": len(fields_meta),
        "fields_meta_modifier_count": 0,
        "fields_meta_modifier_sample": [],
    }}

    if arch:
        root = ET.fromstring(arch)
        native["root_tag"] = root.tag
        field_names = []
        field_seen = set()
        header_labels = []
        box_labels = []
        page_labels = []
        status_fields = []
        for el in root.iter():
            if el.tag == "header":
                for child in list(el):
                    if child.tag != "button":
                        continue
                    label = str(child.get("string") or child.get("name") or "").strip()
                    if label:
                        header_labels.append(label)
            elif el.tag == "div" and "oe_button_box" in str(el.get("class") or ""):
                for child in list(el):
                    if child.tag != "button":
                        continue
                    label = str(child.get("string") or child.get("name") or "").strip()
                    if label:
                        box_labels.append(label)
            elif el.tag == "notebook":
                native["notebook_count"] += 1
            elif el.tag == "page":
                native["page_count"] += 1
                label = str(el.get("string") or el.get("name") or "").strip()
                if label:
                    page_labels.append(label)
            elif el.tag == "group":
                native["group_count"] += 1
            elif el.tag == "field":
                native["field_node_count"] += 1
                fname = str(el.get("name") or "").strip()
                if fname and fname not in field_seen:
                    field_seen.add(fname)
                    field_names.append(fname)
                if str(el.get("widget") or "").strip() == "statusbar" and fname:
                    status_fields.append(fname)
        native["header_buttons_count"] = len(header_labels)
        native["header_buttons_labels"] = header_labels[:20]
        native["button_box_count"] = len(box_labels)
        native["button_box_labels"] = box_labels[:20]
        native["page_labels"] = page_labels[:20]
        native["statusbar_fields"] = status_fields[:20]
        native["field_names_count"] = len(field_names)
        native["field_names_sample"] = field_names[:25]

    modifier_fields = []
    for fname, meta in fields_meta.items():
        mods = (meta or {{}}).get("modifiers") or {{}}
        if mods:
            modifier_fields.append(fname)
    native["fields_meta_modifier_count"] = len(modifier_fields)
    native["fields_meta_modifier_sample"] = sorted(modifier_fields)[:25]

    primary_raw = su_env["app.view.parser"].sudo().parse_odoo_view("project.project", "form")
    if owner._looks_like_parser_wrapper(primary_raw):
        primary = owner._unwrap_contract_shape("form", primary_raw)
    else:
        primary = primary_raw if isinstance(primary_raw, dict) else {{}}

    vcfg = owner._generate_from_fields_view_get("project.project", "form")
    internal_contract = vcfg.get_contract_api(filter_runtime=True, check_model_acl=True)

    primary_types = {{}}
    primary_fields = set()
    walk_layout(primary.get("layout") if isinstance(primary, dict) else [], primary_types, primary_fields)

    internal_types = {{}}
    internal_fields = set()
    walk_layout(internal_contract.get("layout") if isinstance(internal_contract, dict) else [], internal_types, internal_fields)

    def extend_button_box(block):
        rows = []
        for key in ("button_box", "stat_buttons"):
            chunk = block.get(key) if isinstance(block, dict) and isinstance(block.get(key), list) else []
            rows.extend(chunk)
        return rows

    primary_button_box = extend_button_box(primary)
    internal_button_box = extend_button_box(internal_contract)

    primary_summary = {{
        "layout_type_counts": primary_types,
        "layout_field_names_count": len(primary_fields),
        "layout_field_names_sample": sorted(primary_fields)[:25],
        "statusbar_field": ((primary.get("statusbar") or {{}}).get("field") if isinstance(primary.get("statusbar"), dict) else None),
        "header_buttons_count": len(primary.get("header_buttons") or []) if isinstance(primary, dict) else 0,
        "header_buttons_labels": [key_of(x) for x in (primary.get("header_buttons") or []) if key_of(x)][:20] if isinstance(primary, dict) else [],
        "button_box_count": len(primary_button_box),
        "button_box_labels": [key_of(x) for x in primary_button_box if key_of(x)][:20],
        "field_modifiers_count": len((primary.get("field_modifiers") or {{}})) if isinstance(primary, dict) else 0,
        "field_modifiers_sample": sorted(((primary.get("field_modifiers") or {{}}).keys()))[:25] if isinstance(primary, dict) else [],
    }}

    internal_summary = {{
        "layout_type_counts": internal_types,
        "layout_field_names_count": len(internal_fields),
        "layout_field_names_sample": sorted(internal_fields)[:25],
        "statusbar_field": ((internal_contract.get("statusbar") or {{}}).get("field") if isinstance(internal_contract.get("statusbar"), dict) else None),
        "header_buttons_count": len(internal_contract.get("header_buttons") or []) if isinstance(internal_contract, dict) else 0,
        "header_buttons_labels": [key_of(x) for x in (internal_contract.get("header_buttons") or []) if key_of(x)][:20] if isinstance(internal_contract, dict) else [],
        "button_box_count": len(internal_button_box),
        "button_box_labels": [key_of(x) for x in internal_button_box if key_of(x)][:20],
        "field_modifiers_count": len((internal_contract.get("field_modifiers") or {{}})) if isinstance(internal_contract, dict) else 0,
        "field_modifiers_sample": sorted(((internal_contract.get("field_modifiers") or {{}}).keys()))[:25] if isinstance(internal_contract, dict) else [],
    }}

    gaps = []

    def flag(condition, key, detail):
        if condition:
            gaps.append({{"key": key, "detail": detail}})

    flag(native["header_buttons_count"] > primary_summary["header_buttons_count"], "primary.header_buttons", "native header button count exceeds parser output")
    flag(native["button_box_count"] > primary_summary["button_box_count"], "primary.button_box", "native button_box count exceeds parser output")
    flag(native["notebook_count"] > int(primary_types.get("notebook", 0)), "primary.layout.notebook", "native notebook count exceeds parser layout output")
    flag(native["page_count"] > int(primary_types.get("page", 0)), "primary.layout.page", "native page count exceeds parser layout output")
    flag(native["group_count"] > int(primary_types.get("group", 0)), "primary.layout.group", "native group count exceeds parser layout output")
    flag(bool(native["statusbar_fields"]) and primary_summary["statusbar_field"] not in native["statusbar_fields"], "primary.statusbar", "native statusbar field not preserved in parser output")

    flag(native["header_buttons_count"] > internal_summary["header_buttons_count"], "internal_contract.header_buttons", "native header button count exceeds internal contract output")
    flag(native["button_box_count"] > internal_summary["button_box_count"], "internal_contract.button_box", "native button_box count exceeds internal contract output")
    flag(native["notebook_count"] > int(internal_types.get("notebook", 0)), "internal_contract.layout.notebook", "native notebook count exceeds internal contract layout output")
    flag(native["page_count"] > int(internal_types.get("page", 0)), "internal_contract.layout.page", "native page count exceeds internal contract layout output")
    flag(native["group_count"] > int(internal_types.get("group", 0)), "internal_contract.layout.group", "native group count exceeds internal contract layout output")
    flag(bool(native["statusbar_fields"]) and internal_summary["statusbar_field"] not in native["statusbar_fields"], "internal_contract.statusbar", "native statusbar field not preserved in internal contract")

    payload = {{
        "status": "PASS",
        "native": native,
        "primary_parser": primary_summary,
        "internal_contract": internal_summary,
        "gap_count": len(gaps),
        "gaps": gaps,
    }}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
"""


def login(intent_url: str, db: str, login_name: str, password: str) -> str:
    status, resp = http_post_json(
        intent_url,
        {"intent": "login", "params": {"db": db, "login": login_name, "password": password}},
        headers={"X-Anonymous-Intent": "1"},
    )
    require_ok(status, resp, f"login({login_name})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    token = str(session.get("token") or data.get("token") or "").strip()
    if not token:
        raise RuntimeError(f"login({login_name}) missing token")
    return token


def fetch_live_form(intent_url: str, token: str) -> tuple[dict, list[dict]]:
    status, resp = http_post_json(
        intent_url,
        {
            "intent": "ui.contract",
            "params": {"op": "model", "model": "project.project", "view_type": "form", "contract_mode": "user"},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract(project.project.form)")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    top_buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    return form, top_buttons


def walk_layout(nodes: list[dict], type_counter: dict[str, int], field_names: set[str]) -> None:
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        ntype = str(node.get("type") or "").strip()
        if ntype:
            type_counter[ntype] = type_counter.get(ntype, 0) + 1
        fname = str(node.get("name") or "").strip()
        if ntype == "field" and fname:
            field_names.add(fname)
        walk_layout(node.get("children") if isinstance(node.get("children"), list) else [], type_counter, field_names)


def key_of(row: dict) -> str:
    if not isinstance(row, dict):
        return ""
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    return str(
        row.get("key")
        or row.get("label")
        or row.get("string")
        or row.get("name")
        or payload.get("method")
        or payload.get("ref")
        or ""
    ).strip()


def summarize_form_block(block: dict, top_buttons: list[dict]) -> dict:
    layout_types: dict[str, int] = {}
    layout_fields: set[str] = set()
    walk_layout(block.get("layout") if isinstance(block.get("layout"), list) else [], layout_types, layout_fields)
    button_box: list[dict] = []
    for key in ("button_box", "stat_buttons"):
        rows = block.get(key)
        if isinstance(rows, list):
            button_box.extend(rows)
    return {
        "layout_type_counts": layout_types,
        "layout_field_names_count": len(layout_fields),
        "layout_field_names_sample": sorted(layout_fields)[:25],
        "statusbar_field": ((block.get("statusbar") or {}).get("field") if isinstance(block.get("statusbar"), dict) else None),
        "header_buttons_count": len(block.get("header_buttons") or []) if isinstance(block.get("header_buttons"), list) else 0,
        "header_buttons_labels": [key_of(x) for x in (block.get("header_buttons") or []) if key_of(x)][:20] if isinstance(block.get("header_buttons"), list) else [],
        "button_box_count": len(button_box),
        "button_box_labels": [key_of(x) for x in button_box if key_of(x)][:20],
        "field_modifiers_count": len(block.get("field_modifiers") or {}) if isinstance(block.get("field_modifiers"), dict) else 0,
        "field_modifiers_sample": sorted((block.get("field_modifiers") or {}).keys())[:25] if isinstance(block.get("field_modifiers"), dict) else [],
        "visible_fields_count": len(block.get("visible_fields") or []) if isinstance(block.get("visible_fields"), list) else 0,
        "top_buttons_count": len(top_buttons),
        "top_buttons_labels": [key_of(x) for x in top_buttons if key_of(x)][:20],
    }


def append_gap(native: dict, summary: dict, prefix: str, gaps: list[dict]) -> None:
    types = summary.get("layout_type_counts") if isinstance(summary.get("layout_type_counts"), dict) else {}
    if native["header_buttons_count"] > summary["header_buttons_count"]:
        gaps.append({"key": f"{prefix}.header_buttons", "detail": "native header button count exceeds parsed output"})
    if native["button_box_count"] > summary["button_box_count"]:
        gaps.append({"key": f"{prefix}.button_box", "detail": "native button_box count exceeds parsed output"})
    if native["notebook_count"] > int(types.get("notebook", 0)):
        gaps.append({"key": f"{prefix}.layout.notebook", "detail": "native notebook count exceeds parsed output"})
    if native["page_count"] > int(types.get("page", 0)):
        gaps.append({"key": f"{prefix}.layout.page", "detail": "native page count exceeds parsed output"})
    if native["group_count"] > int(types.get("group", 0)):
        gaps.append({"key": f"{prefix}.layout.group", "detail": "native group count exceeds parsed output"})
    if native["statusbar_fields"] and summary.get("statusbar_field") not in native["statusbar_fields"]:
        gaps.append({"key": f"{prefix}.statusbar", "detail": "native statusbar field not preserved"})


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.db, args.login)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "python3", "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "docker exec failed\n")
        return result.returncode or 1

    payload = json.loads(result.stdout)
    if args.password:
        base_url = get_base_url()
        intent_url = f"{base_url}/api/v1/intent?db={args.db}"
        token = login(intent_url, args.db, args.login, args.password)
        live_form, top_buttons = fetch_live_form(intent_url, token)
        live_summary = summarize_form_block(live_form, top_buttons)
        payload["live_ui_contract"] = live_summary
        gaps = payload.get("gaps") if isinstance(payload.get("gaps"), list) else []
        append_gap(payload["native"], live_summary, "live_ui_contract", gaps)
        payload["gap_count"] = len(gaps)

    sys.stdout.write(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
