#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_delivery_menu_integrity_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "product_delivery_menu_integrity_guard.md"
EXPECTED_SCENE_KEYS = [
    "projects.intake",
    "project.management",
    "cost",
    "payment",
    "settlement",
    "my_work.workspace",
]
ALLOWED_MENU_KEY_PREFIXES = ("system.",)


def _write(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")


def _write_json(path: Path, payload: dict) -> None:
    _write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _post(intent_url: str, token: str | None, intent: str, params: dict | None = None, *, db_name: str = ""):
    headers = {"X-Anonymous-Intent": "1"} if token is None else {"Authorization": f"Bearer {token}"}
    if db_name:
        headers["X-Odoo-DB"] = db_name
    status, payload = http_post_json(intent_url, {"intent": intent, "params": params or {}}, headers=headers)
    return status, payload if isinstance(payload, dict) else {}


def _assert_ok(status: int, payload: dict, label: str) -> None:
    if status >= 400 or payload.get("ok") is not True:
        raise RuntimeError(f"{label} failed: status={status} payload={payload}")


def _extract_token(login_payload: dict) -> str:
    data = login_payload.get("data") if isinstance(login_payload.get("data"), dict) else {}
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _flatten_leaf_rows(contract: dict) -> list[dict]:
    out: list[dict] = []

    def _walk(nodes: list[dict] | None) -> None:
        for node in nodes or []:
            if not isinstance(node, dict):
                continue
            children = node.get("children") if isinstance(node.get("children"), list) else []
            if children:
                _walk(children)
                continue
            out.append(node)

    _walk(contract.get("nav") if isinstance(contract.get("nav"), list) else [])
    return out


def _menu_key(row: dict) -> str:
    return str((row.get("meta") or {}).get("menu_key") or row.get("key") or "").strip()


def _route(row: dict) -> str:
    return str((row.get("meta") or {}).get("route") or "").strip()


def _scene_key(row: dict) -> str:
    return str((row.get("meta") or {}).get("scene_key") or "").strip()


def _action_id(row: dict) -> int:
    value = (row.get("meta") or {}).get("action_id")
    try:
        return int(value or 0)
    except Exception:
        return 0


def _model(row: dict) -> str:
    return str((row.get("meta") or {}).get("model") or "").strip()


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "demo_pm").strip()
    password = str(os.getenv("E2E_PASSWORD") or "demo").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "db_name": db_name, "login": login}
    try:
        status, login_resp = _post(intent_url, None, "login", {"db": db_name, "login": login, "password": password}, db_name=db_name)
        _assert_ok(status, login_resp, "login")
        token = _extract_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, init_resp = _post(intent_url, token, "system.init", {"scene": "web", "with_preload": False, "root_xmlid": "smart_construction_core.menu_sc_root"}, db_name=db_name)
        _assert_ok(status, init_resp, "system.init")
        data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        contract = data.get("delivery_engine_v1") if isinstance(data.get("delivery_engine_v1"), dict) else {}
        if not contract:
            raise RuntimeError("delivery_engine_v1 missing")

        rows = _flatten_leaf_rows(contract)
        if not rows:
            raise RuntimeError("nav leaf rows missing")
        menu_keys = [_menu_key(row) for row in rows]
        non_empty_menu_keys = [key for key in menu_keys if key]
        if not non_empty_menu_keys:
            raise RuntimeError("menu keys missing")
        invalid_menu_keys = [
            key for key in non_empty_menu_keys if not any(key.startswith(prefix) for prefix in ALLOWED_MENU_KEY_PREFIXES)
        ]
        if invalid_menu_keys:
            raise RuntimeError(f"menu key prefix drift: {invalid_menu_keys[:8]}")

        seen = set()
        duplicates = []
        for key in non_empty_menu_keys:
            if key in seen:
                duplicates.append(key)
            seen.add(key)
        if duplicates:
            raise RuntimeError(f"duplicate menu keys: {sorted(set(duplicates))[:8]}")

        context_missing = []
        nav_scene_keys = set()
        for row in rows:
            key = _menu_key(row)
            route = _route(row)
            scene_key = _scene_key(row)
            action_id = _action_id(row)
            model = _model(row)
            if scene_key:
                nav_scene_keys.add(scene_key)
            if not (route or scene_key or action_id > 0 or model):
                context_missing.append(key or str(row.get("key") or ""))
        if context_missing:
            raise RuntimeError(f"menu context missing: {context_missing[:8]}")

        scenes = contract.get("scenes") if isinstance(contract.get("scenes"), list) else []
        runtime_scene_keys = [str(row.get("scene_key") or "").strip() for row in scenes if isinstance(row, dict)]
        if runtime_scene_keys != EXPECTED_SCENE_KEYS:
            raise RuntimeError(f"scene keys drift: {runtime_scene_keys}")

        overlapping_scene_keys = sorted(scene_key for scene_key in runtime_scene_keys if scene_key in nav_scene_keys)
        if not overlapping_scene_keys:
            raise RuntimeError("nav leaves missing runtime scene-key overlap")

        report["leaf_count"] = len(rows)
        report["menu_key_count"] = len(non_empty_menu_keys)
        report["scene_keys"] = runtime_scene_keys
        report["nav_scene_keys"] = sorted(nav_scene_keys)
        report["scene_overlap_keys"] = overlapping_scene_keys
    except Exception as exc:
        report["status"] = "FAIL"
        report["error"] = str(exc)
        _write_json(OUT_JSON, report)
        _write(OUT_MD, f"# Delivery Menu Integrity Guard\n\n- status: `FAIL`\n- error: `{exc}`\n")
        print("[product_delivery_menu_integrity_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    _write(OUT_MD, "# Delivery Menu Integrity Guard\n\n- status: `PASS`\n")
    print("[product_delivery_menu_integrity_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
