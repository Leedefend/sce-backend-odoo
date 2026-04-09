#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT_DIR = Path(os.environ.get("ROOT_DIR", Path(__file__).resolve().parents[2]))
ODOO_RUNTIME = ROOT_DIR / "runtime" / "odoo"
if str(ODOO_RUNTIME) not in sys.path:
    sys.path.append(str(ODOO_RUNTIME))

odoo = None
api = None
config = None
MenuFactService = None
MenuTargetInterpreterService = None
RUNTIME_AVAILABLE = True


def _load_odoo_runtime() -> None:
    global odoo, api, config, MenuFactService, MenuTargetInterpreterService, RUNTIME_AVAILABLE
    if odoo is not None:
        return
    import importlib
    try:
        odoo = importlib.import_module("odoo")
        api = importlib.import_module("odoo.api")
        config = importlib.import_module("odoo.tools").config
        MenuFactService = importlib.import_module(
            "odoo.addons.smart_core.delivery.menu_fact_service"
        ).MenuFactService
        MenuTargetInterpreterService = importlib.import_module(
            "odoo.addons.smart_core.delivery.menu_target_interpreter_service"
        ).MenuTargetInterpreterService
        RUNTIME_AVAILABLE = True
    except Exception:
        RUNTIME_AVAILABLE = False


def _resolve_uid(env, login: str) -> int:
    if not login:
        return odoo.SUPERUSER_ID
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    if not user:
        raise ValueError(f"user login not found: {login}")
    return int(user.id)


def _fact_node(node: dict) -> dict:
    children = node.get("children") if isinstance(node.get("children"), list) else []
    menu_id = node.get("menu_id")
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(children),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "children": [_fact_node(child) for child in children],
    }


def _flat_fact_node(node: dict) -> dict:
    menu_id = node.get("menu_id")
    child_ids = node.get("child_ids") if isinstance(node.get("child_ids"), list) else []
    return {
        "menu_id": menu_id,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": node.get("parent_id"),
        "complete_name": str(node.get("complete_name") or ""),
        "sequence": node.get("sequence"),
        "groups": node.get("groups") if isinstance(node.get("groups"), list) else [],
        "web_icon": str(node.get("web_icon") or ""),
        "has_children": bool(child_ids),
        "action_raw": str(node.get("action_raw") or ""),
        "action_type": str(node.get("action_type") or ""),
        "action_id": node.get("action_id"),
        "action_exists": bool(node.get("action_exists")),
        "action_meta": node.get("action_meta") if isinstance(node.get("action_meta"), dict) else {},
        "child_ids": child_ids,
    }


def export_navigation_snapshot(db_name: str, user_login: str, output: Path) -> Path:
    _load_odoo_runtime()
    if not RUNTIME_AVAILABLE:
        payload = {
            "meta": {
                "db": db_name,
                "user_login": user_login or "__superuser__",
                "status": "SKIP",
                "reason": "odoo_runtime_not_available",
            },
            "nav_fact": {"flat": [], "tree": []},
            "nav_explained": {"flat": [], "tree": []},
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output
    config["db_name"] = db_name
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        bootstrap_env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        uid = _resolve_uid(bootstrap_env, user_login)
        env = api.Environment(cr, uid, {})
        facts = MenuFactService(env).export_visible_menu_facts()
        nav_fact = {
            "flat": [_flat_fact_node(node) for node in facts.flat],
            "tree": [_fact_node(node) for node in facts.tree],
        }
        nav_explained = MenuTargetInterpreterService(env).interpret(nav_fact, scene_map={}, policy={})
        payload = {
            "meta": {
                "db": db_name,
                "user_login": user_login or "__superuser__",
                "user_id": uid,
                "nav_fact_count": len(nav_fact.get("flat") or []),
                "nav_explained_count": len(nav_explained.get("flat") or []),
            },
            "nav_fact": nav_fact,
            "nav_explained": nav_explained,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Export menu navigation interpreted snapshot.")
    parser.add_argument("--db", default=os.environ.get("DB_NAME", "sc_demo"), help="database name")
    parser.add_argument("--user-login", default="", help="user login for visibility snapshot")
    parser.add_argument(
        "--output",
        default=str(ROOT_DIR / "artifacts" / "menu" / "menu_navigation_snapshot_v1.json"),
        help="output snapshot path",
    )
    args = parser.parse_args()
    out = export_navigation_snapshot(db_name=args.db, user_login=args.user_login, output=Path(args.output))
    print(f"[menu.target.navigation.snapshot] PASS snapshot={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
