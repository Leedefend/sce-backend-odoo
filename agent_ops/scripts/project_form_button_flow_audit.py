#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit project form button flow across dispatch/finalize/ui.contract")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    return parser.parse_args()


def build_probe_code(login: str) -> str:
    return f"""
import json
from odoo import api, SUPERUSER_ID
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler

user = env["res.users"].sudo().search([("login", "=", {login!r})], limit=1)
if not user:
    raise SystemExit("user not found")

ctx = dict(env.context or {{}})
user_env = api.Environment(env.cr, user.id, ctx)
su_env = api.Environment(env.cr, SUPERUSER_ID, ctx)

def bucket_rows(form):
    form = form if isinstance(form, dict) else {{}}
    out = {{}}
    for bucket in ("header_buttons", "button_box", "stat_buttons"):
        rows = form.get(bucket) if isinstance(form.get(bucket), list) else []
        out[bucket] = rows
    return out

def project_rows(rows):
    rows = rows if isinstance(rows, list) else []
    selected = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {{}}
        method = str(payload.get("method") or row.get("name") or "").strip().lower()
        label = str(row.get("label") or row.get("string") or "").strip()
        key = str(row.get("key") or "").strip()
        if method == "action_view_tasks" or "view_tasks" in key.lower() or "create project" in label.lower():
            selected.append({{
                "key": key,
                "label": label,
                "level": str(row.get("level") or "").strip(),
                "selection": str(row.get("selection") or "").strip(),
                "method": method,
            }})
    return selected

dispatcher = ActionDispatcher(user_env, su_env)
dispatch_data, versions = dispatcher.dispatch({{"subject":"model","model":"project.project","view_type":"form","with_data":False}})
dispatch_form = (((dispatch_data or {{}}).get("views") or {{}}).get("form") or {{}})

cs = ContractService(user_env)
fixed = cs.finalize_contract({{"ok": True, "data": dispatch_data, "meta": {{"subject":"model"}}}})
fixed_data = fixed.get("data") if isinstance(fixed.get("data"), dict) else {{}}
fixed_form = (((fixed_data or {{}}).get("views") or {{}}).get("form") or {{}})

handler = UiContractHandler(user_env)
ui_res = handler.handle({{"op":"model","model":"project.project","view_type":"form","contract_mode":"user"}})
ui_data = ui_res.get("data") if isinstance(ui_res.get("data"), dict) else {{}}
ui_form = (((ui_data or {{}}).get("views") or {{}}).get("form") or {{}})

payload = {{
    "status": "PASS",
    "user_id": user.id,
    "dispatch": {{
        "buttons": project_rows((dispatch_data or {{}}).get("buttons")),
        "form_buckets": {{k: project_rows(v) for k, v in bucket_rows(dispatch_form).items()}},
    }},
    "finalize": {{
        "buttons": project_rows((fixed_data or {{}}).get("buttons")),
        "form_buckets": {{k: project_rows(v) for k, v in bucket_rows(fixed_form).items()}},
    }},
    "ui_contract": {{
        "buttons": project_rows((ui_data or {{}}).get("buttons")),
        "form_buckets": {{k: project_rows(v) for k, v in bucket_rows(ui_form).items()}},
    }},
}}
print(json.dumps(payload, ensure_ascii=False, indent=2))
"""


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.login)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "odoo", "shell", "-c", "/var/lib/odoo/odoo.conf", "-d", args.db],
        input=code,
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
