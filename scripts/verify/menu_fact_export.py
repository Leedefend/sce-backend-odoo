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


def _load_odoo_runtime() -> None:
    global odoo, api, config, MenuFactService
    if odoo is not None:
        return
    import importlib

    odoo = importlib.import_module("odoo")
    api = importlib.import_module("odoo.api")
    config = importlib.import_module("odoo.tools").config
    MenuFactService = importlib.import_module(
        "odoo.addons.smart_core.delivery.menu_fact_service"
    ).MenuFactService


def _resolve_uid(env, login: str) -> int:
    if not login:
        return odoo.SUPERUSER_ID
    user = env["res.users"].sudo().search([("login", "=", login)], limit=1)
    if not user:
        raise ValueError(f"user login not found: {login}")
    return int(user.id)


def export_menu_facts(db_name: str, user_login: str, output: Path) -> Path:
    _load_odoo_runtime()
    config["db_name"] = db_name
    registry = odoo.registry(db_name)
    with registry.cursor() as cr:
        bootstrap_env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        uid = _resolve_uid(bootstrap_env, user_login)
        env = api.Environment(cr, uid, {})
        service = MenuFactService(env)
        snapshot = service.export_visible_menu_facts()
        payload = {
            "meta": {
                "db": db_name,
                "user_login": user_login or "__superuser__",
                "user_id": uid,
                "menu_total": len(snapshot.flat),
            },
            "flat": snapshot.flat,
            "tree": snapshot.tree,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Export ir.ui.menu facts snapshot (facts-only).")
    parser.add_argument("--db", default=os.environ.get("DB_NAME", "sc_demo"), help="database name")
    parser.add_argument("--user-login", default="", help="user login for visibility snapshot")
    parser.add_argument(
        "--output",
        default=str(ROOT_DIR / "artifacts" / "menu" / "menu_fact_snapshot_v1.json"),
        help="output snapshot path",
    )
    args = parser.parse_args()

    out = export_menu_facts(db_name=args.db, user_login=args.user_login, output=Path(args.output))
    print(f"[menu.fact.export] PASS snapshot={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
