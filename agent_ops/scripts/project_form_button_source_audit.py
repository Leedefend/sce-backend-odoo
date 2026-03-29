#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit project form button source path inside running Odoo container")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    return parser.parse_args()


def build_probe_code(db: str, login: str) -> str:
    return f"""
import json
import odoo
from odoo import api, SUPERUSER_ID
from odoo.tools import config

config.parse_config(["-c", "/var/lib/odoo/odoo.conf", "-d", {db!r}])
registry = odoo.registry({db!r})
with registry.cursor() as cr:
    su_env = api.Environment(cr, SUPERUSER_ID, {{}})
    user = su_env["res.users"].search([("login", "=", {login!r})], limit=1)
    if not user:
        raise SystemExit("user not found")

    owner = su_env["app.view.config"]
    view_data = owner._safe_get_view_data("project.project", "form")

    def key_of(row):
        if not isinstance(row, dict):
            return ""
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {{}}
        return str(
            row.get("key")
            or row.get("name")
            or payload.get("method")
            or payload.get("ref")
            or row.get("string")
            or row.get("label")
            or ""
        ).strip()

    raw_buttons = owner._extract_top_buttons(view_data) if hasattr(owner, "_extract_top_buttons") else []
    raw_form = owner._generate_from_fields_view_get("project.project", "form")
    raw_arch_parsed = raw_form.arch_parsed or {{}}
    raw_form_view = raw_arch_parsed if isinstance(raw_arch_parsed, dict) else {{}}

    primary_raw = su_env["app.view.parser"].sudo().parse_odoo_view("project.project", "form")
    if owner._looks_like_parser_wrapper(primary_raw):
        primary = owner._unwrap_contract_shape("form", primary_raw)
    else:
        primary = primary_raw if isinstance(primary_raw, dict) else {{}}

    final_contract = raw_form.get_contract_api(filter_runtime=True, check_model_acl=True)
    final_views = final_contract.get("views") if isinstance(final_contract.get("views"), dict) else {{}}
    final_form = final_views.get("form") if isinstance(final_views.get("form"), dict) else {{}}
    final_buttons = final_contract.get("buttons") if isinstance(final_contract.get("buttons"), list) else []

    payload = {{
        "status": "PASS",
        "user_id": user.id,
        "raw_top_buttons_count": len(raw_buttons) if isinstance(raw_buttons, list) else 0,
        "raw_top_buttons_keys": [key_of(x) for x in (raw_buttons or []) if key_of(x)][:20],
        "primary_header_buttons_count": len((primary.get("header_buttons") or [])) if isinstance(primary, dict) else 0,
        "primary_header_buttons_keys": [key_of(x) for x in (primary.get("header_buttons") or []) if key_of(x)][:20] if isinstance(primary, dict) else [],
        "primary_button_box_count": len((primary.get("button_box") or [])) if isinstance(primary, dict) else 0,
        "primary_button_box_keys": [key_of(x) for x in (primary.get("button_box") or []) if key_of(x)][:20] if isinstance(primary, dict) else [],
        "primary_stat_buttons_count": len((primary.get("stat_buttons") or [])) if isinstance(primary, dict) else 0,
        "primary_stat_buttons_keys": [key_of(x) for x in (primary.get("stat_buttons") or []) if key_of(x)][:20] if isinstance(primary, dict) else [],
        "arch_parsed_header_buttons_count": len((raw_form_view.get("header_buttons") or [])) if isinstance(raw_form_view, dict) else 0,
        "arch_parsed_header_buttons_keys": [key_of(x) for x in (raw_form_view.get("header_buttons") or []) if key_of(x)][:20] if isinstance(raw_form_view, dict) else [],
        "arch_parsed_button_box_count": len((raw_form_view.get("button_box") or [])) if isinstance(raw_form_view, dict) else 0,
        "arch_parsed_button_box_keys": [key_of(x) for x in (raw_form_view.get("button_box") or []) if key_of(x)][:20] if isinstance(raw_form_view, dict) else [],
        "arch_parsed_stat_buttons_count": len((raw_form_view.get("stat_buttons") or [])) if isinstance(raw_form_view, dict) else 0,
        "arch_parsed_stat_buttons_keys": [key_of(x) for x in (raw_form_view.get("stat_buttons") or []) if key_of(x)][:20] if isinstance(raw_form_view, dict) else [],
        "final_contract_buttons_count": len(final_buttons),
        "final_contract_buttons_keys": [key_of(x) for x in final_buttons if key_of(x)][:20],
        "final_form_header_buttons_count": len((final_form.get("header_buttons") or [])) if isinstance(final_form, dict) else 0,
        "final_form_header_buttons_keys": [key_of(x) for x in (final_form.get("header_buttons") or []) if key_of(x)][:20] if isinstance(final_form, dict) else [],
        "final_form_button_box_count": len((final_form.get("button_box") or [])) if isinstance(final_form, dict) else 0,
        "final_form_button_box_keys": [key_of(x) for x in (final_form.get("button_box") or []) if key_of(x)][:20] if isinstance(final_form, dict) else [],
        "final_form_stat_buttons_count": len((final_form.get("stat_buttons") or [])) if isinstance(final_form, dict) else 0,
        "final_form_stat_buttons_keys": [key_of(x) for x in (final_form.get("stat_buttons") or []) if key_of(x)][:20] if isinstance(final_form, dict) else [],
    }}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
"""


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.db, args.login)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "python3", "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "docker exec failed\\n")
        return result.returncode or 1
    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
