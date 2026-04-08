#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
import urllib.request
from http.cookiejar import CookieJar


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


def _norm(value) -> str:
    return str(value or "").strip().lower()


class SessionClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post(self, path: str, payload: dict, headers: dict | None = None) -> tuple[int, dict]:
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", **(headers or {})},
            method="POST",
        )
        with self.opener.open(request, timeout=30) as response:
            body = json.loads(response.read().decode("utf-8"))
            return int(response.status), body

    def authenticate(self, db_name: str, login: str, password: str) -> int:
        status, body = self.post(
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

    def call_kw(self, model: str, method: str, args: list, kwargs: dict | None = None):
        status, body = self.post(
            "/web/dataset/call_kw",
            {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": args,
                    "kwargs": kwargs or {},
                },
                "id": int(time.time()),
            },
        )
        if status != 200:
            raise RuntimeError(f"call_kw status={status} model={model} method={method}")
        if body.get("error"):
            raise RuntimeError(str(body.get("error")))
        return body.get("result")


def _collect_keys(node: dict) -> set[str]:
    keys = set()
    for key in ["xmlid", "menu_xmlid", "action_xmlid", "scene_key", "model", "key", "menu_id", "id", "action_id"]:
        value = _norm(node.get(key))
        if value:
            keys.add(value)
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    for key in ["xmlid", "menu_xmlid", "action_xmlid", "scene_key", "model", "menu_id", "action_id"]:
        value = _norm(meta.get(key))
        if value:
            keys.add(value)
    return keys


def _allowed_keys(role_entries: list[dict], role_code: str) -> set[str]:
    role = _norm(role_code)
    allowed = set()
    for group in role_entries:
        if not isinstance(group, dict):
            continue
        code = _norm(group.get("role_code"))
        if not code:
            continue
        if code != "__global__" and code != role:
            continue
        for entry in group.get("entries") or []:
            if not isinstance(entry, dict):
                continue
            if not bool(entry.get("is_enabled")):
                continue
            key = _norm(entry.get("entry_key"))
            if key:
                allowed.add(key)
    return allowed


def _filter_tree(tree: list[dict], allowed: set[str]) -> list[dict]:
    if not tree or not allowed:
        return tree

    def walk(nodes: list[dict]) -> list[dict]:
        kept = []
        for node in nodes:
            children = walk(node.get("children") or [])
            matched = any(key in allowed for key in _collect_keys(node))
            if matched or children:
                cloned = dict(node)
                cloned["children"] = children
                kept.append(cloned)
        return kept

    filtered = walk(tree)
    return filtered if filtered else tree


def _is_clickable(node: dict) -> bool:
    meta = node.get("meta") if isinstance(node.get("meta"), dict) else {}
    action_id = int(meta.get("action_id") or node.get("action_id") or 0)
    menu_id = int(node.get("menu_id") or node.get("id") or meta.get("menu_id") or 0)
    route = str((node.get("target") or {}).get("route") or "").strip() if isinstance(node.get("target"), dict) else ""
    return action_id > 0 or menu_id > 0 or bool(route)


def _walk_leafs(nodes: list[dict]) -> list[dict]:
    out = []
    for node in nodes:
        children = node.get("children") or []
        if children:
            out.extend(_walk_leafs(children))
        else:
            out.append(node)
    return out


def main() -> None:
    base_url = _env("E2E_BASE_URL", "http://localhost:8069")
    db_name = _env("DB_NAME", "sc_test")
    outsider_login = _env("ROLE_OUTSIDER_LOGIN", "sc_fx_pure_outsider")

    admin_client = SessionClient(base_url)
    admin_uid = admin_client.authenticate(db_name, "admin", "admin")
    if admin_uid <= 0:
        raise SystemExit("[native_business_admin_config_role_entry_clickpath_evidence_verify] FAIL admin auth failed")

    company_id = 1
    admin_self = admin_client.call_kw("res.users", "read", [[admin_uid], ["company_id"]], {})
    if isinstance(admin_self, list) and admin_self:
        row = admin_self[0] if isinstance(admin_self[0], dict) else {}
        company_raw = row.get("company_id")
        if isinstance(company_raw, list) and company_raw:
            company_id = int(company_raw[0] or 1)

    temp_login = f"sc_tmp_outsider_{int(time.time())}"
    created = admin_client.call_kw(
        "res.users",
        "create",
        [[{
            "name": "Temp Outsider Verify",
            "login": temp_login,
            "password": "demo",
            "sc_role_profile": "owner",
            "company_id": company_id,
            "company_ids": [(6, 0, [company_id])],
        }]],
        {},
    )
    if isinstance(created, list):
        created = created[0] if created else 0
    temp_user_id = int(created or 0)
    if temp_user_id <= 0:
        raise SystemExit("[native_business_admin_config_role_entry_clickpath_evidence_verify] FAIL temp outsider create failed")

    roles = [
        ("admin", "admin", ["admin"]),
        ("pm", "sc_fx_pm", ["demo", "prod_like", "admin"]),
        ("finance", "sc_fx_finance", ["demo", "prod_like", "admin"]),
        ("outsider", outsider_login, ["demo", "prod_like", "admin"]),
        ("outsider_controlled", temp_login, ["demo"]),
    ]

    failures: list[str] = []
    details: list[str] = []

    try:
        for role, login, passwords in roles:
            client = None
            uid = 0
            for password in passwords:
                probe = SessionClient(base_url)
                uid = probe.authenticate(db_name, login, password)
                if uid > 0:
                    client = probe
                    break
            if not client:
                failures.append(f"{role}: auth failed")
                continue

            status, body = client.post(
                "/api/v1/intent",
                {"intent": "system.init", "params": {"contract_mode": "user"}},
                headers={"X-Anonymous-Intent": "1"},
            )

            if role == "outsider_controlled":
                if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
                    details.append(f"{role}:uid={uid},deny-envelope=status{status}")
                    continue

            if status != 200 or not isinstance(body, dict) or body.get("ok") is not True:
                failures.append(f"{role}: system.init failed status={status}")
                continue

            data = body.get("data") if isinstance(body.get("data"), dict) else {}
            nav = data.get("nav") if isinstance(data.get("nav"), list) else []
            role_entries = data.get("role_entries") if isinstance(data.get("role_entries"), list) else []
            role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
            role_code = str(role_surface.get("role_code") or "").strip()

            allowed = _allowed_keys(role_entries, role_code)
            filtered = _filter_tree(nav, allowed)
            leafs = _walk_leafs(filtered)
            clickable_leafs = [node for node in leafs if _is_clickable(node)]

            if role in {"pm", "finance"} and not clickable_leafs:
                failures.append(f"{role}: no clickable leaf after filtering")

            if role in {"outsider", "outsider_controlled"}:
                outsider_specific = [
                    node for node in clickable_leafs
                    if any(k in {"project.list", "payment.request"} for k in _collect_keys(node))
                ]
                if outsider_specific:
                    failures.append(f"{role}: found project/payment specific clickable entries")

            details.append(
                f"{role}:uid={uid},role_code={role_code or '-'},allowed={len(allowed)},leaf={len(leafs)},clickable={len(clickable_leafs)}"
            )
    finally:
        try:
            admin_client.call_kw("res.users", "unlink", [[temp_user_id]], {})
        except Exception:
            pass

    if failures:
        raise SystemExit("[native_business_admin_config_role_entry_clickpath_evidence_verify] FAIL " + "; ".join(failures))

    print("[native_business_admin_config_role_entry_clickpath_evidence_verify] PASS " + " | ".join(details))


if __name__ == "__main__":
    main()
