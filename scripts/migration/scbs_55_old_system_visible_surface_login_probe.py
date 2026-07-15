#!/usr/bin/env python3
"""Verify SCBS55 old-system visible lists through a real user login.

The destination and credentials are validated by the shared online-capture
preflight before any request is created.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402

INPUT_CSV = REPO_ROOT / "docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv"
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_55_old_system_visible_surface_login_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "scbs_55_old_system_visible_surface_login_probe_report_v1.md"


def clean(value: object) -> str:
    return str(value or "").strip()


def split_items(raw: str) -> list[str]:
    return [item.strip() for item in str(raw or "").split(";") if item.strip()]


def item_label(raw: str) -> str:
    text = clean(raw)
    return text.split("(", 1)[0].strip() if "(" in text else text


def csv_visible_labels(row: dict[str, str]) -> list[str]:
    return [item_label(item) for item in split_items(row.get("visible_columns", ""))]


def config_id_from_link(link: str) -> str:
    query = parse_qs(urlparse(link).query)
    values = query.get("ConfigId") or query.get("configId") or query.get("configid") or []
    return clean(values[0]) if values else ""


def old_base_url(login_url: str) -> str:
    parsed = urlparse(login_url)
    path = parsed.path.rstrip("/")
    marker = "/System/User/Login"
    if path.endswith(marker):
        path = path[: -len(marker)]
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")


def login(session: requests.Session, base_url: str, username: str, password: str) -> dict[str, Any]:
    payload = {
        "Type": "Common",
        "Param": {
            "UserName": username,
            "IsEncrypt": False,
            "Password": password,
            "PasswordMd5": hashlib.md5(password.encode("utf-8")).hexdigest(),
            "VerificationCodeKey": "",
            "VerificationCode": "",
            "EncryptLockKey": "",
            "PhoneNumber": "",
            "SMSVerificationCodeKey": "",
            "SMSVerificationCode": "",
        },
    }
    response = session.post(
        f"{base_url}/api/System/UserApi/Login",
        json=payload,
        timeout=30,
        headers={"Referer": f"{base_url}/System/User/Login"},
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000" or not body.get("Data", {}).get("Token"):
        raise RuntimeError({"old_system_login_failed": {"Code": body.get("Code"), "Msg": body.get("Msg")}})
    return body["Data"]


def api_get(session: requests.Session, base_url: str, token: str, path: str) -> dict[str, Any]:
    response = session.get(
        urljoin(f"{base_url}/api/", path),
        headers={"Token": token, "Referer": base_url + "/"},
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_get_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body


def api_post(session: requests.Session, base_url: str, token: str, path: str, data: dict[str, Any]) -> dict[str, Any]:
    response = session.post(
        urljoin(f"{base_url}/api/", path),
        json=data,
        headers={"Token": token, "Referer": base_url + "/"},
        timeout=45,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_post_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body


def visible_labels_from_config(config: dict[str, Any]) -> list[str]:
    detail = json.loads(config["DETAIL_CONFIG"])
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig", [])
    labels: list[str] = []

    def visit(items: list[dict[str, Any]]) -> None:
        for item in items or []:
            info = item.get("Info") or {}
            if info.get("IsHide") is True:
                continue
            name = clean(info.get("Name"))
            if name:
                labels.append(name)
            children = item.get("ChildConfig")
            if children:
                visit(children)

    visit(columns)
    return labels


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 Old System Visible Surface Login Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Old User: {payload['old_user']['UserName']} / {payload['old_user']['PersonName']}",
        f"Old Project: {payload['old_user']['ProjectName']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | group | name | menu visible | config fetched | field match | note |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {group} | {name} | {menu_visible} | {config_fetched} | {field_match} | {note} |".format(
                **row
            )
        )
    lines.extend(["", "## Failures", "", "```json", json.dumps(payload["failures"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def main() -> int:
    config = require_online_capture(("scbs",))["scbs"]
    login_url = f"{config.base_url.rstrip('/')}/System/User/Login"
    username = os.getenv("OLD_SCBS_USERNAME")
    password = os.getenv("OLD_SCBS_PASSWORD")
    if not username or not password:
        raise RuntimeError("OLD_SCBS_USERNAME and OLD_SCBS_PASSWORD are required")

    rows = list(csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")))
    base_url = old_base_url(login_url)
    session = requests.Session()
    user_info = login(session, base_url, username, password)
    token = user_info["Token"]
    home = api_post(session, base_url, token, "HomeApi/GetCommonHomeInfo", {})
    menu_rows = home.get("Data", {}).get("MenuInfoArr") or []
    menus_by_config: dict[str, list[dict[str, Any]]] = {}
    for menu in menu_rows:
        config_id = config_id_from_link(clean(menu.get("LINK_URL")))
        if config_id:
            menus_by_config.setdefault(config_id, []).append(menu)

    result_rows: list[dict[str, Any]] = []
    for row in rows:
        config_id = clean(row.get("config_id"))
        expected_labels = csv_visible_labels(row)
        menu_matches = menus_by_config.get(config_id, []) if config_id else []
        if not menu_matches:
            # Some SCBS55 entries are native/custom/report/dashboard menus with
            # no LowCode List ConfigId. They still need real-login visibility.
            menu_matches = [
                menu
                for menu in menu_rows
                if row["name"] in {clean(menu.get("MENU_NAME")), clean(menu.get("DEFAULT_NAME"))}
            ]
        actual_labels: list[str] = []
        config_fetched = False
        note = ""
        if config_id and row.get("config_type") == "List":
            config_body = api_get(session, base_url, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")
            config_fetched = True
            actual_labels = visible_labels_from_config(config_body["Data"])
        elif not expected_labels:
            note = "no list field contract in SCBS55 CSV"
        field_match = actual_labels == expected_labels if expected_labels else True
        if expected_labels and not field_match:
            note = "old runtime visible labels differ from captured CSV"
        result_rows.append(
            {
                "seq": int(row["seq"]),
                "group": row["group"],
                "name": row["name"],
                "config_id": config_id,
                "menu_visible": bool(menu_matches),
                "menu_names": [clean(item.get("MENU_NAME")) for item in menu_matches],
                "config_fetched": config_fetched,
                "expected_labels": expected_labels,
                "actual_labels": actual_labels,
                "field_match": field_match,
                "note": note,
            }
        )

    failures = [
        item
        for item in result_rows
        if not item["menu_visible"] or (item["expected_labels"] and not item["field_match"])
    ]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "scbs_55_old_system_visible_surface_login_probe",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "old_login_url": login_url,
        "old_user": {
            "UserId": user_info.get("UserId"),
            "UserName": user_info.get("UserName"),
            "PersonName": user_info.get("PersonName"),
            "ProjectId": user_info.get("ProjectId"),
            "ProjectName": user_info.get("ProjectName"),
            "CompanyId": user_info.get("CompanyId"),
            "CompanyName": user_info.get("CompanyName"),
        },
        "old_menu_count": len(menu_rows),
        "row_count": len(result_rows),
        "checked_list_config_count": len([item for item in result_rows if item["config_fetched"]]),
        "field_match_count": len([item for item in result_rows if item["expected_labels"] and item["field_match"]]),
        "failure_count": len(failures),
        "failures": failures,
        "rows": result_rows,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    write_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    OUTPUT_JSON.write_text(write_text, encoding="utf-8")
    OUTPUT_REPORT.write_text(report_markdown(payload), encoding="utf-8")
    print("SCBS_55_OLD_SYSTEM_VISIBLE_SURFACE_LOGIN_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
