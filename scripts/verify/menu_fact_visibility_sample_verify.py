#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


REQUIRED_NODE_FIELDS = {
    "menu_id",
    "key",
    "name",
    "parent_id",
    "complete_name",
    "sequence",
    "groups",
    "web_icon",
    "has_children",
    "action_raw",
    "action_type",
    "action_id",
    "action_exists",
    "action_meta",
}


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


class OdooSession:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def _post(self, path: str, payload: dict):
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Anonymous-Intent": "1"},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            return int(response.status), body

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        status, body = self._post(
            "/web/session/authenticate",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {"db": db_name, "login": login, "password": password},
                "id": 1,
            },
        )
        if status != 200:
            return 0
        result = body.get("result") if isinstance(body, dict) else {}
        return int((result or {}).get("uid") or 0)

    def menu_tree(self) -> tuple[int, dict]:
        status, body = self._post(
            "/api/menu/tree",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {},
                "id": 2,
            },
        )
        if isinstance(body, dict) and isinstance(body.get("result"), dict):
            return status, body.get("result")
        return status, body if isinstance(body, dict) else {}

    def call_kw(self, model: str, method: str, args: list | None = None, kwargs: dict | None = None):
        status, body = self._post(
            f"/web/dataset/call_kw/{model}/{method}",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args or [],
                    "kwargs": kwargs or {},
                },
                "id": 3,
            },
        )
        if status != 200:
            raise RuntimeError(f"call_kw http={status}")
        if isinstance(body, dict) and body.get("error"):
            raise RuntimeError(json.dumps(body.get("error"), ensure_ascii=False))
        if isinstance(body, dict):
            return body.get("result")
        raise RuntimeError("invalid call_kw response")


def _login(base_url: str, db_name: str, login: str, passwords: list[str]) -> tuple[OdooSession | None, str]:
    for pwd in passwords:
        session = OdooSession(base_url)
        uid = session.authenticate(db_name, login, pwd)
        if uid > 0:
            return session, pwd
    return None, ""


def _check_node_fields(node: dict) -> tuple[bool, list[str]]:
    keys = set(node.keys())
    missing = sorted(list(REQUIRED_NODE_FIELDS - keys))
    errors = []
    if missing:
        errors.append(f"missing_fields:{','.join(missing)}")
    if not isinstance(node.get("groups"), list):
        errors.append("groups_not_list")
    if not isinstance(node.get("action_meta"), dict):
        errors.append("action_meta_not_dict")
    return (len(errors) == 0), errors


def _flatten_legacy_tree(node: dict) -> list[dict]:
    if not isinstance(node, dict):
        return []
    menu_id = node.get("id")
    action_id = node.get("action") if isinstance(node.get("action"), int) else None
    children = node.get("children") if isinstance(node.get("children"), list) else []
    current = {
        "menu_id": menu_id if isinstance(menu_id, int) else None,
        "key": f"menu:{menu_id}" if isinstance(menu_id, int) else "menu:unknown",
        "name": str(node.get("name") or ""),
        "parent_id": None,
        "complete_name": "",
        "sequence": None,
        "groups": [],
        "web_icon": "",
        "has_children": bool(children),
        "action_raw": str(action_id) if isinstance(action_id, int) else "",
        "action_type": "",
        "action_id": action_id,
        "action_exists": bool(action_id),
        "action_meta": {},
    }
    out = [current]
    for child in children:
        out.extend(_flatten_legacy_tree(child))
    return out


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_demo")
    roles = [
        ("admin", _env("ROLE_ADMIN_LOGIN", "admin"), [_env("ROLE_ADMIN_PASSWORD", "admin")]),
        ("pm", _env("ROLE_PM_LOGIN", "sc_fx_pm"), ["demo", "prod_like", "admin"]),
        ("finance", _env("ROLE_FINANCE_LOGIN", "sc_fx_finance"), ["demo", "prod_like", "admin"]),
    ]

    rows = []
    failures = []
    admin_menu_ids: set[int] = set()

    for role, login, pwds in roles:
        session, used = _login(base_url, db_name, login, [pwd for pwd in pwds if pwd])
        if not session:
            failures.append(f"{role}:auth_failed")
            continue
        status, body = session.menu_tree()
        if status != 200 or body.get("ok") is not True:
            failures.append(f"{role}:menu_tree_not_ok")
            continue

        schema_mode = "facts_v1"
        flat = []
        nav_fact = body.get("nav_fact") if isinstance(body.get("nav_fact"), dict) else {}
        if isinstance(nav_fact.get("flat"), list):
            flat = nav_fact.get("flat")
        elif isinstance(body.get("menu"), dict):
            schema_mode = "legacy_tree"
            flat = _flatten_legacy_tree(body.get("menu"))
        else:
            failures.append(f"{role}:menu_payload_missing")
            continue

        menu_ids = {
            int(node.get("menu_id"))
            for node in flat
            if isinstance(node, dict) and isinstance(node.get("menu_id"), int)
        }

        node_errors: list[str] = []
        if schema_mode == "facts_v1":
            for node in flat:
                if not isinstance(node, dict):
                    node_errors.append("invalid_node_type")
                    continue
                ok, errors = _check_node_fields(node)
                if not ok:
                    node_errors.extend(errors)

        if role == "admin":
            admin_menu_ids = set(menu_ids)
            if not admin_menu_ids:
                node_errors.append("admin_menu_empty")
        elif admin_menu_ids:
            leaked = sorted(list(menu_ids - admin_menu_ids))
            if leaked:
                node_errors.append(f"menu_not_in_admin_scope:{len(leaked)}")

        if node_errors:
            failures.append(f"{role}:" + ";".join(sorted(set(node_errors))[:8]))

        rows.append(
            {
                "role": role,
                "login": login,
                "password_used": used,
                "schema_mode": schema_mode,
                "menu_count": len(menu_ids),
                "node_count": len(flat),
                "field_check_pass": len(node_errors) == 0,
            }
        )

    result = "PASS" if not failures else "FAIL"
    payload = {
        "base_url": base_url,
        "db": db_name,
        "result": result,
        "rows": rows,
        "failures": failures,
    }
    out_path = Path("artifacts/menu/menu_fact_visibility_sample_v1.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if failures:
        raise SystemExit("[menu.fact.visibility_sample] FAIL " + " | ".join(failures))
    print("[menu.fact.visibility_sample] PASS " + " | ".join([f"{r['role']}:{r['menu_count']}" for r in rows]))


if __name__ == "__main__":
    main()
