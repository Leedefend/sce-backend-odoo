#!/usr/bin/env python3
"""Capture SCBS55 old-system add/show form surfaces through a real user login.

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
from urllib.parse import urljoin, urlparse

import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from scripts.verify.online_capture_security import require_online_capture  # noqa: E402

INPUT_CSV = REPO_ROOT / "docs/migration_alignment/scbs_55_user_visible_surface_live_alignment_v1.csv"
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(REPO_ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_55_old_system_form_surface_login_probe_result_v1.json"
OUTPUT_REPORT = ARTIFACT_ROOT / "scbs_55_old_system_form_surface_login_probe_report_v1.md"


def clean(value: object) -> str:
    return str(value or "").strip()


def old_base_url(login_url: str) -> str:
    parsed = urlparse(login_url)
    path = parsed.path.rstrip("/")
    marker = "/System/User/Login"
    if path.endswith(marker):
        path = path[: -len(marker)]
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")


def truthy_hide(value: object) -> bool:
    return value is True or clean(value).lower() in {"true", "1", "yes"}


def as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def config_dict(component: dict[str, Any]) -> dict[str, Any]:
    config = component.get("Config")
    if isinstance(config, dict):
        return config
    if isinstance(config, list):
        for item in config:
            if isinstance(item, dict):
                return item
    return {}


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
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"old_system_get_failed": path, "Code": body.get("Code"), "Msg": body.get("Msg")})
    return body


def section_names(detail: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for item in (detail.get("Collapse") or {}).get("GroupList") or []:
        info = item.get("Info") or {}
        if truthy_hide(info.get("IsHide")):
            continue
        name = clean(info.get("Name"))
        if name:
            names.append(name)
    return names


def form_item_label(item: dict[str, Any]) -> str:
    form_info = as_dict(item.get("FormItemConfig")).get("Info") or {}
    component_info = config_dict(as_dict(item.get("CustomComponent"))).get("Info") or {}
    if truthy_hide(form_info.get("IsHide")) or truthy_hide(component_info.get("IsHide")):
        return ""
    return clean(form_info.get("Name") or component_info.get("Name"))


def main_table_fields(detail: dict[str, Any]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for table in detail.get("MainTable") or []:
        section = clean(table.get("CollapseName"))
        for item in table.get("FormItemList") or []:
            label = form_item_label(item)
            if not label:
                continue
            info = (item.get("FormItemConfig") or {}).get("Info") or {}
            component = as_dict(item.get("CustomComponent"))
            config = config_dict(component)
            fields.append(
                {
                    "section": section,
                    "label": label,
                    "rule_name": clean(info.get("RuleName")),
                    "component": clean(component.get("Path")),
                    "data_config": "/".join(clean(value) for value in (config.get("DataConfig") or []) if clean(value)),
                    "readonly": clean((config.get("Info") or {}).get("Readonly")),
                }
            )
    return fields


def from_table_fields(detail: dict[str, Any]) -> list[dict[str, str]]:
    fields: list[dict[str, str]] = []
    for table in detail.get("FromTable") or []:
        section = clean(table.get("CollapseName"))
        table_config = table.get("TableConfig") or {}
        for column in table_config.get("ColumnConfig") or []:
            info = column.get("Info") or {}
            if truthy_hide(info.get("IsHide")):
                continue
            label = clean(info.get("Name"))
            if label:
                fields.append(
                    {
                        "section": section,
                        "label": label,
                        "field": clean(info.get("Field") or info.get("Code")),
                        "component": clean(as_dict(column.get("CustomComponent")).get("Path")),
                    }
                )
    return fields


def load_form_config(session: requests.Session, base_url: str, token: str, config_id: str) -> dict[str, Any]:
    body = api_get(session, base_url, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")
    data = body["Data"]
    detail = json.loads(data["DETAIL_CONFIG"])
    return {
        "config_id": config_id,
        "config_name": clean(data.get("CONFIGNAME")),
        "config_type": clean(data.get("CONFIGTYPE")),
        "title": clean(((detail.get("TopBar") or {}).get("Info") or {}).get("TitleName")),
        "sections": section_names(detail),
        "main_fields": main_table_fields(detail),
        "line_fields": from_table_fields(detail),
        "has_file_section": any(
            clean(((item.get("CustomComponent") or {}).get("Path"))) == "form/FormFile.vue"
            for item in (detail.get("Collapse") or {}).get("GroupList") or []
        ),
        "has_approval": bool(detail.get("Approval")),
    }


def report_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBS55 Old System Form Surface Login Probe v1",
        "",
        f"Status: {payload['status']}",
        f"Old User: {payload['old_user']['UserName']} / {payload['old_user']['PersonName']}",
        f"Old Project: {payload['old_user']['ProjectName']}",
        f"Generated At: {payload['generated_at']}",
        "",
        "| seq | group | name | add fields | show fields | sections | file | approval | status |",
        "| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["rows"]:
        lines.append(
            "| {seq} | {group} | {name} | {add_field_count} | {show_field_count} | {section_count} | "
            "{has_file_section} | {has_approval} | {status} |".format(**row)
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

    result_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for row in rows:
        add_config_id = clean(row.get("add_config_id"))
        show_config_id = clean(row.get("show_add_config_id"))
        result: dict[str, Any] = {
            "seq": int(row["seq"]),
            "group": row["group"],
            "name": row["name"],
            "target_model": row.get("target_model", ""),
            "add_config_id": add_config_id,
            "show_add_config_id": show_config_id,
            "add": None,
            "show": None,
            "status": "SKIP_NO_FORM_CONFIG",
        }
        try:
            if add_config_id:
                result["add"] = load_form_config(session, base_url, token, add_config_id)
            if show_config_id:
                result["show"] = load_form_config(session, base_url, token, show_config_id)
            if add_config_id or show_config_id:
                result["status"] = "PASS"
        except Exception as exc:
            result["status"] = "FAIL_FETCH_FORM_CONFIG"
            result["error"] = repr(exc)

        add = result.get("add") or {}
        show = result.get("show") or {}
        add_fields = (add.get("main_fields") or []) + (add.get("line_fields") or [])
        show_fields = (show.get("main_fields") or []) + (show.get("line_fields") or [])
        sections = add.get("sections") or show.get("sections") or []
        result.update(
            {
                "add_field_count": len(add_fields),
                "show_field_count": len(show_fields),
                "section_count": len(sections),
                "has_file_section": bool(add.get("has_file_section") or show.get("has_file_section")),
                "has_approval": bool(add.get("has_approval") or show.get("has_approval")),
            }
        )
        if str(result["status"]).startswith("FAIL"):
            failures.append(result)
        result_rows.append(result)

    payload = {
        "status": "PASS" if not failures else "FAIL",
        "mode": "scbs_55_old_system_form_surface_login_probe",
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
        "row_count": len(result_rows),
        "form_config_count": len([item for item in result_rows if item["status"] != "SKIP_NO_FORM_CONFIG"]),
        "failure_count": len(failures),
        "failures": failures,
        "rows": result_rows,
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_REPORT.write_text(report_markdown(payload), encoding="utf-8")
    print(
        "SCBS_55_OLD_SYSTEM_FORM_SURFACE_LOGIN_PROBE="
        + json.dumps(
            {
                "status": payload["status"],
                "row_count": payload["row_count"],
                "form_config_count": payload["form_config_count"],
                "failure_count": payload["failure_count"],
                "output_json": str(OUTPUT_JSON),
                "output_report": str(OUTPUT_REPORT),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
