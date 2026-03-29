#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit project form button governance path inside running Odoo container")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    return parser.parse_args()


def build_probe_code(db: str, login: str) -> str:
    return f"""
import json
from odoo import api, SUPERUSER_ID
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.utils.contract_governance import apply_contract_governance

user = env["res.users"].sudo().search([("login", "=", {login!r})], limit=1)
if not user:
    raise SystemExit("user not found")

ctx = dict(env.context or {{}})
user_env = api.Environment(env.cr, user.id, ctx)
su_env = api.Environment(env.cr, SUPERUSER_ID, ctx)
dispatcher = ActionDispatcher(user_env, su_env)
dispatch_data, versions = dispatcher.dispatch({{"subject":"model","model":"project.project","view_type":"form","with_data":False}})

def keys(rows):
    out = []
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {{}}
        key = str(
            row.get("key")
            or row.get("name")
            or payload.get("method")
            or payload.get("ref")
            or row.get("string")
            or row.get("label")
            or ""
        ).strip()
        if key:
            out.append(key)
    return out

dispatch_buttons = dispatch_data.get("buttons") if isinstance(dispatch_data, dict) and isinstance(dispatch_data.get("buttons"), list) else []
dispatch_toolbar = dispatch_data.get("toolbar") if isinstance(dispatch_data, dict) and isinstance(dispatch_data.get("toolbar"), dict) else {{}}

cs = ContractService(user_env)
fixed = cs.finalize_contract({{"ok": True, "data": dispatch_data, "meta": {{"subject":"model"}}}})
fixed_data = fixed.get("data") if isinstance(fixed.get("data"), dict) else {{}}
fixed_buttons = fixed_data.get("buttons") if isinstance(fixed_data.get("buttons"), list) else []
fixed_toolbar = fixed_data.get("toolbar") if isinstance(fixed_data.get("toolbar"), dict) else {{}}

governed = apply_contract_governance(
    dict(fixed_data),
    "user",
    contract_surface="governed",
    source_mode="",
    inject_contract_mode=False,
)
governed_buttons = governed.get("buttons") if isinstance(governed.get("buttons"), list) else []
governed_toolbar = governed.get("toolbar") if isinstance(governed.get("toolbar"), dict) else {{}}
governed_action_groups = governed.get("action_groups") if isinstance(governed.get("action_groups"), list) else []

payload = {{
    "status": "PASS",
    "user_id": user.id,
    "dispatch": {{
        "buttons_count": len(dispatch_buttons),
        "buttons_keys": keys(dispatch_buttons)[:20],
        "toolbar_header_count": len(dispatch_toolbar.get("header") or []) if isinstance(dispatch_toolbar, dict) else 0,
        "toolbar_sidebar_count": len(dispatch_toolbar.get("sidebar") or []) if isinstance(dispatch_toolbar, dict) else 0,
        "toolbar_footer_count": len(dispatch_toolbar.get("footer") or []) if isinstance(dispatch_toolbar, dict) else 0,
    }},
    "finalize_contract": {{
        "buttons_count": len(fixed_buttons),
        "buttons_keys": keys(fixed_buttons)[:20],
        "toolbar_header_count": len(fixed_toolbar.get("header") or []) if isinstance(fixed_toolbar, dict) else 0,
        "toolbar_sidebar_count": len(fixed_toolbar.get("sidebar") or []) if isinstance(fixed_toolbar, dict) else 0,
        "toolbar_footer_count": len(fixed_toolbar.get("footer") or []) if isinstance(fixed_toolbar, dict) else 0,
    }},
    "governed": {{
        "buttons_count": len(governed_buttons),
        "buttons_keys": keys(governed_buttons)[:20],
        "toolbar_header_count": len(governed_toolbar.get("header") or []) if isinstance(governed_toolbar, dict) else 0,
        "toolbar_sidebar_count": len(governed_toolbar.get("sidebar") or []) if isinstance(governed_toolbar, dict) else 0,
        "toolbar_footer_count": len(governed_toolbar.get("footer") or []) if isinstance(governed_toolbar, dict) else 0,
        "action_group_count": len(governed_action_groups),
        "action_group_keys": [str((row or {{}}).get("key") or "").strip() for row in governed_action_groups[:20] if isinstance(row, dict)],
    }},
}}
print(json.dumps(payload, ensure_ascii=False, indent=2))
"""


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.db, args.login)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "odoo", "shell", "-c", "/var/lib/odoo/odoo.conf", "-d", args.db],
        input=code,
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
