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
    parser = argparse.ArgumentParser(description="Audit field-set mismatch between finalized native layout and governed project form contract")
    parser.add_argument("--db", required=True)
    parser.add_argument("--login", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--container", required=True)
    parser.add_argument("--action-id", type=int, required=True)
    parser.add_argument("--record-id", type=int, required=True)
    return parser.parse_args()


def build_probe_code(db: str, login: str, action_id: int, record_id: int) -> str:
    return f"""
import json
import sys
import odoo
import odoo.addons
from odoo import api, SUPERUSER_ID
from odoo.tools import config

config.parse_config(["-c", "/var/lib/odoo/odoo.conf", "-d", {db!r}])
if "/mnt/extra-addons" not in sys.path:
    sys.path.insert(0, "/mnt/extra-addons")
addons_ns = getattr(odoo.addons, "__path__", None)
if addons_ns is not None and "/mnt/extra-addons" not in addons_ns:
    addons_ns.append("/mnt/extra-addons")

from odoo.addons.smart_core.handlers.ui_contract import UiContractHandler
from odoo.addons.smart_core.app_config_engine.services.contract_service import ContractService
from odoo.addons.smart_core.utils.contract_governance import apply_contract_governance
from odoo.addons.smart_core.core.native_view_contract_projection import inject_primary_view_projection

registry = odoo.registry({db!r})


def walk_layout(nodes, page=None, page_fields=None, all_fields=None):
    if page_fields is None:
        page_fields = {{}}
    if all_fields is None:
        all_fields = []
    for node in nodes or []:
        if not isinstance(node, dict):
            continue
        ntype = str(node.get("type") or node.get("kind") or "").strip().lower()
        current_page = page
        if ntype == "page":
            current_page = str(node.get("name") or node.get("label") or node.get("string") or "").strip()
            if current_page:
                page_fields.setdefault(current_page, [])
        if ntype == "field":
            fname = str(node.get("name") or "").strip()
            if fname:
                if fname not in all_fields:
                    all_fields.append(fname)
                if current_page and fname not in page_fields.setdefault(current_page, []):
                    page_fields[current_page].append(fname)
        for key in ("children", "tabs", "pages", "nodes", "items"):
            child = node.get(key)
            if isinstance(child, list):
                walk_layout(child, current_page, page_fields, all_fields)
    return page_fields, all_fields


with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {{}})
    user = env["res.users"].search([("login", "=", {login!r})], limit=1)
    runtime = api.Environment(cr, user.id, {{}})
    dispatcher = UiContractHandler(runtime)._build_dispatcher({{}})
    payload = {{
        "subject": "action",
        "action_id": int({action_id}),
        "record_id": int({record_id}),
        "view_type": "form",
        "with_data": False,
    }}
    dispatched, _ = dispatcher.dispatch(payload)
    finalized = ContractService(runtime).finalize_contract({{"ok": True, "data": dispatched, "meta": {{"subject": "action"}}}})
    finalized_data = finalized.get("data", {{}}) or {{}}
    inject_primary_view_projection(finalized_data, requested_view_type="form")

    governed = apply_contract_governance(json.loads(json.dumps(finalized_data)), "user", inject_contract_mode=False)

    finalized_layout = (((finalized_data.get("views") or {{}}).get("form") or {{}}).get("layout") or [])
    governed_layout = (((governed.get("views") or {{}}).get("form") or {{}}).get("layout") or [])
    finalized_page_fields, finalized_layout_fields = walk_layout(finalized_layout)
    governed_page_fields, governed_layout_fields = walk_layout(governed_layout)
    finalized_fields = [name for name in ((finalized_data.get("fields") or {{}}).keys())]
    governed_fields = [name for name in ((governed.get("fields") or {{}}).keys())]

    per_page_gap = {{}}
    for page_name, names in finalized_page_fields.items():
        missing_in_governed_fields = [name for name in names if name not in governed_fields]
        missing_in_governed_layout = [name for name in names if name not in governed_layout_fields]
        if missing_in_governed_fields or missing_in_governed_layout:
            per_page_gap[page_name] = {{
                "finalized_page_fields": names,
                "missing_in_governed_fields": missing_in_governed_fields,
                "missing_in_governed_layout": missing_in_governed_layout,
            }}

    result = {{
        "status": "PASS",
        "finalized_layout_field_count": len(finalized_layout_fields),
        "governed_layout_field_count": len(governed_layout_fields),
        "finalized_fields_count": len(finalized_fields),
        "governed_fields_count": len(governed_fields),
        "finalized_layout_fields": finalized_layout_fields,
        "governed_layout_fields": governed_layout_fields,
        "finalized_fields": finalized_fields,
        "governed_fields": governed_fields,
        "finalized_page_fields": finalized_page_fields,
        "governed_page_fields": governed_page_fields,
        "per_page_gap": per_page_gap,
    }}
    print(json.dumps(result, ensure_ascii=False, indent=2))
"""


def run_container_probe(container: str, code: str) -> dict:
    proc = subprocess.run(
        ["docker", "exec", container, "python3", "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stdout = proc.stdout.strip()
    start = stdout.find("{")
    end = stdout.rfind("}")
    if start < 0 or end < start:
        raise RuntimeError(f"container probe did not return JSON: {stdout[:500]}")
    return json.loads(stdout[start : end + 1])


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


def fetch_live(intent_url: str, token: str, action_id: int, record_id: int) -> dict:
    payload = {
        "intent": "ui.contract",
        "params": {
            "op": "action_open",
            "action_id": action_id,
            "record_id": record_id,
            "view_type": "form",
            "render_profile": "edit",
            "contract_surface": "user",
            "source_mode": "governance_pipeline",
            "edition_key": "standard",
            "context": {
                "edition_runtime_v1": {
                    "edition_key": "standard",
                    "contract_surface": "user",
                    "source_mode": "governance_pipeline",
                }
            },
            "meta": {
                "edition_runtime_v1": {
                    "edition_key": "standard",
                    "contract_surface": "user",
                    "source_mode": "governance_pipeline",
                }
            },
        },
    }
    status, resp = http_post_json(intent_url, payload, headers={"Authorization": f"Bearer {token}"})
    require_ok(status, resp, "ui.contract(action_open)")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    views = data.get("views") if isinstance(data.get("views"), dict) else {}
    form = views.get("form") if isinstance(views.get("form"), dict) else {}
    layout = form.get("layout") if isinstance(form.get("layout"), list) else []

    def walk_layout(nodes, page=None, page_fields=None, all_fields=None):
        if page_fields is None:
            page_fields = {}
        if all_fields is None:
            all_fields = []
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            ntype = str(node.get("type") or node.get("kind") or "").strip().lower()
            current_page = page
            if ntype == "page":
                current_page = str(node.get("name") or node.get("label") or node.get("string") or "").strip()
                if current_page:
                    page_fields.setdefault(current_page, [])
            if ntype == "field":
                fname = str(node.get("name") or "").strip()
                if fname:
                    if fname not in all_fields:
                        all_fields.append(fname)
                    if current_page and fname not in page_fields.setdefault(current_page, []):
                        page_fields[current_page].append(fname)
            for key in ("children", "tabs", "pages", "nodes", "items"):
                child = node.get(key)
                if isinstance(child, list):
                    walk_layout(child, current_page, page_fields, all_fields)
        return page_fields, all_fields

    page_fields, layout_fields = walk_layout(layout)
    return {
        "live_fields": list((data.get("fields") or {}).keys()) if isinstance(data.get("fields"), dict) else [],
        "live_visible_fields": data.get("visible_fields") if isinstance(data.get("visible_fields"), list) else [],
        "live_layout_fields": layout_fields,
        "live_page_fields": page_fields,
    }


def main() -> int:
    args = parse_args()
    intent_url = f"{get_base_url().rstrip('/')}/api/v1/intent"
    token = login(intent_url, args.db, args.login, args.password)
    container_result = run_container_probe(
        args.container,
        build_probe_code(args.db, args.login, args.action_id, args.record_id),
    )
    live_result = fetch_live(intent_url, token, args.action_id, args.record_id)
    output = {
        "status": "PASS",
        "container_probe": container_result,
        "live_http": live_result,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
