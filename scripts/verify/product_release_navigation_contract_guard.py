#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from python_http_smoke_utils import get_base_url, http_post_json


ROOT = Path(__file__).resolve().parents[2]
OUT_JSON = ROOT / "artifacts" / "backend" / "product_release_navigation_contract_guard.json"
OUT_MD = ROOT / "artifacts" / "backend" / "product_release_navigation_contract_guard.md"
EXPECTED_GROUPS = ["已发布产品", "工作辅助"]
EXPECTED_LABELS = [
    "FR-1 项目立项",
    "FR-2 项目推进",
    "FR-3 成本记录",
    "FR-4 付款记录",
    "FR-5 结算结果",
    "我的工作",
]


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
    if not isinstance(data, dict):
        return ""
    token = str(data.get("token") or "").strip()
    if token:
        return token
    session = data.get("session") if isinstance(data.get("session"), dict) else {}
    return str(session.get("token") or "").strip()


def _flatten_release_labels(contract: dict) -> list[str]:
    labels: list[str] = []
    for root in contract.get("nav") or []:
        if not isinstance(root, dict):
            continue
        for group in root.get("children") or []:
            if not isinstance(group, dict):
                continue
            for child in group.get("children") or []:
                if not isinstance(child, dict):
                    continue
                label = str(child.get("label") or child.get("title") or child.get("name") or "").strip()
                if label:
                    labels.append(label)
    return labels


def _group_labels(contract: dict) -> list[str]:
    labels: list[str] = []
    for root in contract.get("nav") or []:
        if not isinstance(root, dict):
            continue
        for group in root.get("children") or []:
            if not isinstance(group, dict):
                continue
            label = str(group.get("label") or group.get("title") or group.get("name") or "").strip()
            if label:
                labels.append(label)
    return labels


def main() -> int:
    base_url = get_base_url()
    db_name = str(os.getenv("E2E_DB") or os.getenv("DB_NAME") or "").strip()
    login = str(os.getenv("E2E_LOGIN") or "demo_pm").strip()
    password = str(os.getenv("E2E_PASSWORD") or os.getenv("ADMIN_PASSWD") or "demo").strip()
    intent_url = f"{base_url}/api/v1/intent"
    if db_name:
        intent_url = f"{intent_url}?db={db_name}"

    report: dict = {"status": "PASS", "login": login, "db_name": db_name}
    try:
        status, login_resp = _post(
            intent_url,
            None,
            "login",
            {"db": db_name, "login": login, "password": password},
            db_name=db_name,
        )
        _assert_ok(status, login_resp, "login")
        token = _extract_token(login_resp)
        if not token:
            raise RuntimeError("login token missing")

        status, init_resp = _post(
            intent_url,
            token,
            "system.init",
            {"scene": "web", "with_preload": False, "root_xmlid": "smart_construction_core.menu_sc_root"},
            db_name=db_name,
        )
        _assert_ok(status, init_resp, "system.init")
        data = init_resp.get("data") if isinstance(init_resp.get("data"), dict) else {}
        role_surface = data.get("role_surface") if isinstance(data.get("role_surface"), dict) else {}
        release_contract = data.get("release_navigation_v1") if isinstance(data.get("release_navigation_v1"), dict) else {}
        if str(role_surface.get("role_code") or "").strip() != "pm":
            raise RuntimeError(f"role_surface.role_code drift: {role_surface}")
        if not release_contract:
            raise RuntimeError("release_navigation_v1 missing")

        group_labels = _group_labels(release_contract)
        release_labels = _flatten_release_labels(release_contract)
        if group_labels != EXPECTED_GROUPS:
            raise RuntimeError(f"release navigation groups drift: {group_labels}")
        if release_labels != EXPECTED_LABELS:
            raise RuntimeError(f"release navigation labels drift: {release_labels}")

        report["role_surface"] = role_surface
        report["group_labels"] = group_labels
        report["release_labels"] = release_labels
        report["scene_nav_root_labels"] = [
            str(root.get("label") or "").strip()
            for root in (data.get("nav") or [])
            if isinstance(root, dict)
        ]
    except Exception as exc:
        report["status"] = "FAIL"
        report.setdefault("errors", []).append(str(exc))
        _write_json(OUT_JSON, report)
        _write(
            OUT_MD,
            "# Product Release Navigation Contract Guard\n\n"
            f"- status: `FAIL`\n"
            f"- db_name: `{db_name}`\n"
            f"- login: `{login}`\n"
            f"- error: `{str(exc)}`\n",
        )
        print("[product_release_navigation_contract_guard] FAIL")
        print(f" - {exc}")
        return 1

    _write_json(OUT_JSON, report)
    _write(
        OUT_MD,
        "# Product Release Navigation Contract Guard\n\n"
        f"- status: `PASS`\n"
        f"- db_name: `{db_name}`\n"
        f"- login: `{login}`\n"
        f"- role_code: `{report['role_surface'].get('role_code', '')}`\n"
        f"- groups: `{', '.join(report['group_labels'])}`\n"
        f"- release_labels: `{', '.join(report['release_labels'])}`\n",
    )
    print("[product_release_navigation_contract_guard] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
