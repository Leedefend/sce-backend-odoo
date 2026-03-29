#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import subprocess
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit suspicious project form button source inside running Odoo container")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    return parser.parse_args()


def build_probe_code(db: str, login: str) -> str:
    return f"""
import json
from odoo import api, SUPERUSER_ID
from odoo.addons.smart_core.app_config_engine.services.dispatchers.action_dispatcher import ActionDispatcher

target_markers = ["obj_action_view_tasks_create project", "action_view_tasks", "create project", "创建项目"]

def row_key(row):
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

def matches(row):
    key = row_key(row).lower()
    label = str((row or {{}}).get("label") or (row or {{}}).get("string") or "").strip().lower()
    payload = (row or {{}}).get("payload") if isinstance((row or {{}}).get("payload"), dict) else {{}}
    method = str(payload.get("method") or (row or {{}}).get("name") or "").strip().lower()
    merged = f"{{key}} {{label}} {{method}}"
    return any(marker in merged for marker in target_markers)

user = env["res.users"].sudo().search([("login", "=", {login!r})], limit=1)
if not user:
    raise SystemExit("user not found")

ctx = dict(env.context or {{}})
user_env = api.Environment(env.cr, user.id, ctx)
su_env = api.Environment(env.cr, SUPERUSER_ID, ctx)

owner = su_env["app.view.config"]
view_data = owner._safe_get_view_data("project.project", "form")
primary_raw = su_env["app.view.parser"].sudo().parse_odoo_view("project.project", "form")
if owner._looks_like_parser_wrapper(primary_raw):
    primary = owner._unwrap_contract_shape("form", primary_raw)
else:
    primary = primary_raw if isinstance(primary_raw, dict) else {{}}

parser_rows = []
for bucket in ("header_buttons", "button_box", "stat_buttons"):
    rows = primary.get(bucket) if isinstance(primary, dict) and isinstance(primary.get(bucket), list) else []
    for row in rows:
        if isinstance(row, dict) and matches(row):
            parser_rows.append({{"bucket": bucket, "row": row}})

dispatcher = ActionDispatcher(user_env, su_env)
dispatch_data, versions = dispatcher.dispatch({{"subject":"model","model":"project.project","view_type":"form","with_data":False}})
dispatch_rows = dispatch_data.get("buttons") if isinstance(dispatch_data, dict) and isinstance(dispatch_data.get("buttons"), list) else []
suspicious_dispatch = [row for row in dispatch_rows if isinstance(row, dict) and matches(row)]

resolved_actions = []
Action = su_env["ir.actions.actions"]
for row in suspicious_dispatch:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {{}}
    ref = payload.get("ref")
    action_id = None
    try:
        action_id = int(ref)
    except Exception:
        action_id = None
    action_meta = {{}}
    if action_id:
        act = Action.browse(action_id)
        if act.exists():
            action_meta = {{
                "id": act.id,
                "name": act.name,
                "type": act.type,
                "xmlid": act.get_external_id().get(act.id, ""),
            }}
    resolved_actions.append({{
        "key": row_key(row),
        "label": str(row.get("label") or row.get("string") or "").strip(),
        "payload": payload,
        "resolved_action": action_meta,
    }})

payload = {{
    "status": "PASS",
    "user_id": user.id,
    "parser_matches": parser_rows,
    "dispatcher_matches": suspicious_dispatch,
    "resolved_actions": resolved_actions,
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
