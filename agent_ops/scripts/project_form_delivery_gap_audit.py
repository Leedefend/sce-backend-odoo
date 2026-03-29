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
    parser = argparse.ArgumentParser(description="Audit project form delivery drift from internal contract to live ui.contract")
    parser.add_argument("--db", required=True, help="Database name")
    parser.add_argument("--login", required=True, help="User login to resolve")
    parser.add_argument("--password", required=True, help="User password for live ui.contract fetch")
    parser.add_argument("--container", required=True, help="Running Odoo container name")
    parser.add_argument("--action-id", type=int, default=0, help="Optional act_window id used by the real detail page")
    parser.add_argument("--record-id", type=int, default=0, help="Optional record id used by the real detail page")
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


def node_signature(node):
    if not isinstance(node, dict):
        return ""
    attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {{}}
    return str(
        node.get("name")
        or node.get("label")
        or attrs.get("name")
        or attrs.get("string")
        or node.get("type")
        or node.get("kind")
        or ""
    ).strip()


def walk_layout(nodes, type_counter, group_paths=None, page_paths=None, trail=None):
    current_trail = list(trail or [])
    for node in (nodes or []):
        if not isinstance(node, dict):
            continue
        ntype = str(node.get("type") or node.get("kind") or "").strip()
        if ntype:
            type_counter[ntype] = type_counter.get(ntype, 0) + 1
        signature = node_signature(node)
        next_trail = current_trail + ([f"{{ntype}}:{{signature}}" if signature else ntype] if ntype else [])
        if ntype == "group" and group_paths is not None:
            group_paths.append(" > ".join(next_trail))
        if ntype == "page" and page_paths is not None:
            page_paths.append(" > ".join(next_trail))
        for key in ("children", "tabs", "pages", "nodes", "items"):
            walk_layout(node.get(key) or [], type_counter, group_paths, page_paths, next_trail)


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


def summarize(block):
    data = block if isinstance(block, dict) else {{}}
    layout = (((data.get("views") or {{}}).get("form") or {{}}).get("layout") or [])
    counts = {{}}
    group_paths = []
    page_paths = []
    walk_layout(layout, counts, group_paths, page_paths)
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    return {{
        "layout_type_counts": counts,
        "group_paths": group_paths,
        "page_paths": page_paths,
        "top_buttons_count": len(buttons),
        "top_buttons_labels": [key_of(x) for x in buttons if key_of(x)][:20],
    }}


with registry.cursor() as cr:
    base_env = api.Environment(cr, SUPERUSER_ID, {{}})
    user = base_env["res.users"].search([("login", "=", {login!r})], limit=1)
    if not user:
        raise SystemExit("user not found")

    runtime_ctx = {{}}
    runtime_env = api.Environment(cr, user.id, runtime_ctx)
    runtime_su_env = api.Environment(cr, SUPERUSER_ID, runtime_ctx)

    payload_model = {{"subject": "model", "model": "project.project", "view_type": "form", "with_data": False}}
    payload_action = {{
        "subject": "action",
        "action_id": int({action_id}),
        "with_data": False,
    }}
    if int({record_id}) > 0:
        payload_action["record_id"] = int({record_id})
        payload_action["view_type"] = "form"

    dispatcher = UiContractHandler(runtime_env)._build_dispatcher(runtime_ctx)
    dispatched, versions = dispatcher.dispatch(payload_model)

    service = ContractService(runtime_env)
    finalized = service.finalize_contract({{"ok": True, "data": dispatched, "meta": {{"subject": "model"}}}})
    finalized_data = finalized.get("data", {{}}) or {{}}
    inject_primary_view_projection(finalized_data, requested_view_type="form")

    governed = apply_contract_governance(finalized_data, "user", inject_contract_mode=False)
    handler_governed = apply_contract_governance(
        UiContractHandler(runtime_env)._inject_render_hints(
            json.loads(json.dumps(finalized_data)),
            {{"op": "model", "model": "project.project", "view_type": "form", "contract_surface": "user", "source_mode": "governance_pipeline"}},
        ),
        "user",
        contract_surface="user",
        source_mode="governance_pipeline",
        inject_contract_mode=False,
    )

    result = {{
        "status": "PASS",
        "user_id": user.id,
        "dispatcher": summarize(dispatched),
        "finalized": summarize(finalized_data),
        "governed": summarize(governed),
        "handler_governed": summarize(handler_governed),
    }}
    if int({action_id}) > 0:
        action_dispatched, action_versions = dispatcher.dispatch(payload_action)
        action_finalized = service.finalize_contract({{"ok": True, "data": action_dispatched, "meta": {{"subject": "action"}}}})
        action_finalized_data = action_finalized.get("data", {{}}) or {{}}
        inject_primary_view_projection(action_finalized_data, requested_view_type="form")
        action_governed = apply_contract_governance(action_finalized_data, "user", inject_contract_mode=False)
        action_handler_governed = apply_contract_governance(
            UiContractHandler(runtime_env)._inject_render_hints(
                json.loads(json.dumps(action_finalized_data)),
                {{
                    "op": "action_open",
                    "action_id": int({action_id}),
                    "record_id": int({record_id}),
                    "view_type": "form",
                    "render_profile": "edit",
                    "contract_surface": "user",
                    "source_mode": "governance_pipeline",
                }},
            ),
            "user",
            contract_surface="user",
            source_mode="governance_pipeline",
            inject_contract_mode=False,
        )
        result["action_open"] = {{
            "dispatcher": summarize(action_dispatched),
            "finalized": summarize(action_finalized_data),
            "governed": summarize(action_governed),
            "handler_governed": summarize(action_handler_governed),
        }}
    print(json.dumps(result, ensure_ascii=False, indent=2))
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


def fetch_live(intent_url: str, token: str, *, action_id: int = 0, record_id: int = 0) -> dict:
    status, resp = http_post_json(
        intent_url,
        {"intent": "ui.contract", "params": {"op": "model", "model": "project.project", "view_type": "form"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, "ui.contract(project.project.form)")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    layout = (((data.get("views") or {}).get("form") or {}).get("layout") or [])
    counts = {}
    group_paths: list[str] = []
    page_paths: list[str] = []
    def node_signature(node):
        if not isinstance(node, dict):
            return ""
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
        return str(
            node.get("name")
            or node.get("label")
            or attrs.get("name")
            or attrs.get("string")
            or node.get("type")
            or node.get("kind")
            or ""
        ).strip()
    def walk(nodes, trail=None):
        current_trail = list(trail or [])
        for node in (nodes or []):
            if not isinstance(node, dict):
                continue
            ntype = str(node.get("type") or node.get("kind") or "").strip()
            if ntype:
                counts[ntype] = counts.get(ntype, 0) + 1
            signature = node_signature(node)
            next_trail = current_trail + ([f"{ntype}:{signature}" if signature else ntype] if ntype else [])
            if ntype == "group":
                group_paths.append(" > ".join(next_trail))
            if ntype == "page":
                page_paths.append(" > ".join(next_trail))
            for key in ("children", "tabs", "pages", "nodes", "items"):
                walk(node.get(key) or [], next_trail)
    walk(layout)
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    return {
        "layout_type_counts": counts,
        "group_paths": group_paths,
        "page_paths": page_paths,
        "top_buttons_count": len(buttons),
        "top_buttons_labels": [
            str(
                row.get("key")
                or row.get("label")
                or row.get("name")
                or ((row.get("payload") or {}).get("method") if isinstance(row.get("payload"), dict) else "")
                or ""
            ).strip()
            for row in buttons
            if isinstance(row, dict)
        ][:20],
    }


def fetch_live_action(intent_url: str, token: str, *, action_id: int, record_id: int = 0) -> dict:
    params: dict[str, object] = {
        "op": "action_open",
        "action_id": int(action_id),
        "render_profile": "edit",
        "contract_surface": "user",
        "source_mode": "governance_pipeline",
        "edition_key": "standard",
    }
    if record_id > 0:
        params["record_id"] = int(record_id)
    payload = {
        "intent": "ui.contract",
        "params": params,
        "context": {
            "edition_runtime_v1": {
                "requested_edition_key": "standard",
                "effective_edition_key": "standard",
                "routed_edition_key": "standard",
            }
        },
        "meta": {
            "edition_runtime_v1": {
                "requested_edition_key": "standard",
                "effective_edition_key": "standard",
            }
        },
    }
    status, resp = http_post_json(
        intent_url,
        payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    require_ok(status, resp, f"ui.contract(action_open:{action_id})")
    data = resp.get("data") if isinstance(resp.get("data"), dict) else {}
    layout = (((data.get("views") or {}).get("form") or {}).get("layout") or [])
    counts = {}
    group_paths: list[str] = []
    page_paths: list[str] = []
    def node_signature(node):
        if not isinstance(node, dict):
            return ""
        attrs = node.get("attributes") if isinstance(node.get("attributes"), dict) else {}
        return str(
            node.get("name")
            or node.get("label")
            or attrs.get("name")
            or attrs.get("string")
            or node.get("type")
            or node.get("kind")
            or ""
        ).strip()
    def walk(nodes, trail=None):
        current_trail = list(trail or [])
        for node in (nodes or []):
            if not isinstance(node, dict):
                continue
            ntype = str(node.get("type") or node.get("kind") or "").strip()
            if ntype:
                counts[ntype] = counts.get(ntype, 0) + 1
            signature = node_signature(node)
            next_trail = current_trail + ([f"{ntype}:{signature}" if signature else ntype] if ntype else [])
            if ntype == "group":
                group_paths.append(" > ".join(next_trail))
            if ntype == "page":
                page_paths.append(" > ".join(next_trail))
            for key in ("children", "tabs", "pages", "nodes", "items"):
                walk(node.get(key) or [], next_trail)
    walk(layout)
    buttons = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    return {
        "layout_type_counts": counts,
        "group_paths": group_paths,
        "page_paths": page_paths,
        "top_buttons_count": len(buttons),
        "top_buttons_labels": [
            str(
                row.get("key")
                or row.get("label")
                or row.get("name")
                or ((row.get("payload") or {}).get("method") if isinstance(row.get("payload"), dict) else "")
                or ""
            ).strip()
            for row in buttons
            if isinstance(row, dict)
        ][:20],
    }


def main() -> int:
    args = parse_args()
    code = build_probe_code(args.db, args.login, args.action_id, args.record_id)
    result = subprocess.run(
        ["docker", "exec", "-i", args.container, "python3", "-c", code],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout or "docker exec failed\\n")
        return result.returncode or 1

    container_payload = json.loads(result.stdout)
    intent_url = f"{get_base_url().rstrip('/')}/api/v1/intent?db={args.db}"
    token = login(intent_url, args.db, args.login, args.password)
    container_payload["live_ui_contract"] = fetch_live(intent_url, token)
    if args.action_id > 0:
        container_payload["live_ui_contract_action_open"] = fetch_live_action(
            intent_url,
            token,
            action_id=args.action_id,
            record_id=args.record_id,
        )
    sys.stdout.write(json.dumps(container_payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
