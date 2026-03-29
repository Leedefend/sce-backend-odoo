#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit project form parser paths inside running Odoo container")
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
    fields_meta = (view_data or {{}}).get("fields") or {{}}

    def collect_fields_view_modifiers(meta):
        out = {{}}
        for name, desc in (meta or {{}}).items():
            mods = (desc or {{}}).get("modifiers") or {{}}
            if mods:
                out[name] = sorted(mods.keys())
        return out

    fields_view_modifiers = collect_fields_view_modifiers(fields_meta)

    primary_raw = su_env["app.view.parser"].sudo().parse_odoo_view("project.project", "form")
    if owner._looks_like_parser_wrapper(primary_raw):
        primary = owner._unwrap_contract_shape("form", primary_raw)
    else:
        primary = primary_raw if isinstance(primary_raw, dict) else {{}}
    fallback = owner._fallback_parse("project.project", "form", view_data)
    parsed_ok = owner._parsed_ok("form", primary)
    if parsed_ok:
        reconciled = primary if isinstance(primary, dict) else {{}}
    else:
        reconciled = fallback
    vcfg = owner._generate_from_fields_view_get("project.project", "form")
    arch_parsed = vcfg.arch_parsed or {{}}
    final_contract = vcfg.get_contract_api(filter_runtime=True, check_model_acl=True)
    form_block = (final_contract.get("views") or {{}}).get("form") or {{}}

    payload = {{
        "status": "PASS",
        "user_id": user.id,
        "fields_view_modifiers_count": len(fields_view_modifiers),
        "fields_view_modifier_keys_sample": sorted(fields_view_modifiers.keys())[:20],
        "primary_field_modifiers_count": len((primary or {{}}).get("field_modifiers") or {{}}) if isinstance(primary, dict) else 0,
        "fallback_field_modifiers_count": len((fallback or {{}}).get("field_modifiers") or {{}}) if isinstance(fallback, dict) else 0,
        "reconciled_field_modifiers_count": len((reconciled or {{}}).get("field_modifiers") or {{}}) if isinstance(reconciled, dict) else 0,
        "arch_parsed_field_modifiers_count": len((arch_parsed or {{}}).get("field_modifiers") or {{}}) if isinstance(arch_parsed, dict) else 0,
        "contract_form_field_modifiers_count": len((form_block or {{}}).get("field_modifiers") or {{}}) if isinstance(form_block, dict) else 0,
        "primary_keys_sample": sorted((((primary or {{}}).get("field_modifiers") or {{}}).keys()))[:20] if isinstance(primary, dict) else [],
        "fallback_keys_sample": sorted((((fallback or {{}}).get("field_modifiers") or {{}}).keys()))[:20] if isinstance(fallback, dict) else [],
        "reconciled_keys_sample": sorted((((reconciled or {{}}).get("field_modifiers") or {{}}).keys()))[:20] if isinstance(reconciled, dict) else [],
        "contract_keys_sample": sorted((((form_block or {{}}).get("field_modifiers") or {{}}).keys()))[:20] if isinstance(form_block, dict) else [],
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
        sys.stderr.write(result.stderr or result.stdout or "docker exec failed\n")
        return result.returncode or 1
    sys.stdout.write(result.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
