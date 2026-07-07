#!/usr/bin/env python3
"""Dump the current user's SCBSLY menu tree without storing credentials."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests


BASE_URL = os.getenv("OLD_SCBS_BASE_URL", "https://www.builderp.cn/SCBSLY_V2").rstrip("/")
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_current_user_menu_dump_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "scbsly_current_user_menu_dump_v1.md"


def clean(value: object) -> str:
    return str(value or "").strip()


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def config_id_from_link(link: str) -> str:
    query = parse_qs(urlparse(link).query)
    values = query.get("ConfigId") or query.get("configId") or query.get("configid") or []
    return clean(values[0]) if values else ""


def login(session: requests.Session) -> dict[str, Any]:
    username = os.getenv("OLD_SCBS_USERNAME")
    password = os.getenv("OLD_SCBS_PASSWORD")
    if not username or not password:
        raise RuntimeError("OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required")
    payload = {
        "Type": "Common",
        "Param": {
            "UserName": username,
            "IsEncrypt": False,
            "Password": password,
            "PasswordMd5": md5(password),
            "VerificationCodeKey": "",
            "VerificationCode": "",
            "EncryptLockKey": "",
            "PhoneNumber": "",
            "SMSVerificationCodeKey": "",
            "SMSVerificationCode": "",
        },
    }
    response = session.post(f"{BASE_URL}/api/System/UserApi/Login", json=payload, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000" or not body.get("Data", {}).get("Token"):
        raise RuntimeError({"old_login_failed": {"Code": body.get("Code"), "Msg": body.get("Msg")}})
    return body["Data"]


def api_post(session: requests.Session, token: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = session.post(f"{BASE_URL}/api/{path}", json=payload, headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_post_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body


def parent_key(menu: dict[str, Any]) -> str:
    return clean(menu.get("PARENT_ID") or menu.get("PARENTID") or menu.get("PARENT_MENU_ID"))


def menu_key(menu: dict[str, Any]) -> str:
    return clean(menu.get("ID") or menu.get("MENU_ID") or menu.get("MenuId"))


def menu_name(menu: dict[str, Any]) -> str:
    return clean(menu.get("MENU_NAME") or menu.get("DEFAULT_NAME") or menu.get("NAME"))


def build_paths(menus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {menu_key(menu): menu for menu in menus if menu_key(menu)}
    rows: list[dict[str, Any]] = []
    for menu in menus:
        names = [menu_name(menu)]
        seen = {menu_key(menu)}
        current = menu
        while parent_key(current) and parent_key(current) in by_id and parent_key(current) not in seen:
            current = by_id[parent_key(current)]
            seen.add(menu_key(current))
            names.append(menu_name(current))
        names = [name for name in reversed(names) if name]
        link = clean(menu.get("LINK_URL"))
        rows.append(
            {
                "id": menu_key(menu),
                "parent_id": parent_key(menu),
                "name": menu_name(menu),
                "path": "/".join(names),
                "link_url": link,
                "config_id": config_id_from_link(link),
                "raw": {
                    key: menu.get(key)
                    for key in ("ID", "MENU_ID", "MENU_NAME", "DEFAULT_NAME", "PARENT_ID", "LINK_URL", "ICON")
                    if key in menu
                },
            }
        )
    return sorted(rows, key=lambda item: (item["path"], item["id"]))


def report(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Current User Menu Dump v1",
        "",
        f"Status: {payload['status']}",
        f"Base URL: {payload['base_url']}",
        f"Historical User: {payload['old_user'].get('UserName')} / {payload['old_user'].get('PersonName')}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| path | config_id | link |",
        "| --- | --- | --- |",
    ]
    for row in payload["menus"]:
        lines.append(f"| {row['path']} | {row['config_id']} | {row['link_url']} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    session = requests.Session()
    user = login(session)
    home = api_post(session, user["Token"], "HomeApi/GetCommonHomeInfo", {})
    menus = build_paths(home.get("Data", {}).get("MenuInfoArr") or [])
    payload = {
        "status": "PASS",
        "mode": "scbsly_current_user_menu_dump",
        "base_url": BASE_URL,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "menu_count": len(menus),
        "menus": menus,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_REPORT.write_text(report(payload), encoding="utf-8")
    print("SCBSLY_CURRENT_USER_MENU_DUMP=" + json.dumps({"status": payload["status"], "menu_count": len(menus), "output": str(OUTPUT_JSON)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
