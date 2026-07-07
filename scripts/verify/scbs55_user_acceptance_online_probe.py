#!/usr/bin/env python3
"""Probe live historical-source list counts for frozen SCBS55 user acceptance surfaces."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scbs_55_old_system_list_count_probe import api_get, api_post, enclosure_ident, login


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbs55_user_acceptance_online_probe_v1.json"


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"{path} root must be object")
    return payload


def list_api_for(config: dict[str, Any], payload: dict[str, Any]) -> str:
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
    if other.get("ListApi"):
        return str(other["ListApi"]).removeprefix("/api/")
    if other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        return "LowCode/FormApi/ListByProcedure"
    return "LowCode/FormApi/ListByTableName"


def acceptance_list_payload(config: dict[str, Any]) -> dict[str, Any]:
    """Build the same neutral list payload used by the old FormList page.

    The older generic count probe injects a broad DJZT filter. That is useful
    for some historical scans, but it changes the acceptance count for pages
    whose visible default has no selected document-state tab. This probe must
    not invent filters beyond DETAIL_CONFIG.
    """
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
    main = other.get("MainTable") if isinstance(other.get("MainTable"), dict) else {}
    where = deepcopy(detail.get("WhereInfo") if isinstance(detail.get("WhereInfo"), dict) else {})
    payload: dict[str, Any] = {
        "BusinessId": config.get("BUSINESSID"),
        "ConfigId": config.get("ID"),
        "OrderInfo": other.get("OrderInfo") or "pid desc",
        "PageIndex": 1,
        "PageSize": 1,
        "WhereInfo": where,
        "TableName": main.get("TableName"),
        "ShowType": other.get("ShowType") or [],
        "ShowTypeList": other.get("ShowTypeList") or [],
        "BMFiled": other.get("BMFiled"),
        "IsSearchNextGS": other.get("IsSearchNextGS") or False,
        "FWZDFiled": other.get("FWZDFiled"),
        "IsEmptyAllVisible": other.get("IsEmptyAllVisible"),
        "ShowDataToUserIdByDJZT": other.get("ShowDataToUserIdByDJZT"),
        "FieldName": {
            "IdField": main.get("IdField") or "Id",
            "ProjectIdField": main.get("ProjectIdField"),
            "LRRID_Field": main.get("LRRID_Field"),
            "Delete_Field": main.get("Delete_Field"),
            "IsShowAdminProject": other.get("IsShowAdminProject"),
        },
        "EnclosureIdent": enclosure_ident(detail),
        "SpecialUserId": other.get("SpecialUserId") or "",
        "SpecialConfig": other.get("SpecialConfig") or {},
        "IsDelData": False,
        "JudgeDeleteField": main.get("JudgeDeleteField", True),
        "OrderInfoSQL": {"SQLID": "", "IsDesc": False},
    }
    if other.get("SelectSQLID"):
        payload["SelectSQLID"] = other.get("SelectSQLID")
    elif other.get("CustomSelectSql"):
        payload["CustomSelectSql"] = other.get("CustomSelectSql")
    if main.get("IsProjectSearch") is False:
        payload["FieldName"].pop("ProjectIdField", None)
    if other.get("ListDisplayType", {}).get("FromTableShow"):
        payload["ListDisplayType"] = other.get("ListDisplayType")
    return payload


def main() -> int:
    manifest = load_json(MANIFEST)
    surfaces = manifest.get("surfaces")
    if not isinstance(surfaces, list):
        raise RuntimeError("manifest surfaces must be a list")

    import requests

    session = requests.Session()
    user = login(session)
    token = user["Token"]
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for surface in surfaces:
        if not isinstance(surface, dict):
            continue
        old = surface.get("old") if isinstance(surface.get("old"), dict) else {}
        key = str(surface.get("key") or "")
        expected_count = int(old.get("expected_count") or 0)
        try:
            config = api_get(
                session,
                token,
                f"LowCode/FormApi/GetConfigById?Id={old.get('config_id')}&LoadInitData=true",
            )["Data"]
            payload = acceptance_list_payload(config)
            api_path = list_api_for(config, payload)
            body = api_post(session, token, api_path, payload)
            old_count = int(body.get("DataCount") or 0)
            detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
            other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
            main = other.get("MainTable") if isinstance(other.get("MainTable"), dict) else {}
            status = "PASS" if old_count == expected_count and main.get("TableName") == old.get("main_table") else "FAIL"
            row = {
                "key": key,
                "name": surface.get("name"),
                "status": status,
                "config_id": old.get("config_id"),
                "api": api_path,
                "expected_count": expected_count,
                "old_count": old_count,
                "expected_main_table": old.get("main_table"),
                "actual_main_table": main.get("TableName"),
                "payload_policy": "detail_config_without_probe_injected_djzt",
            }
        except Exception as exc:  # noqa: BLE001
            row = {
                "key": key,
                "name": surface.get("name"),
                "status": "FAIL",
                "config_id": old.get("config_id"),
                "expected_count": expected_count,
                "old_count": None,
                "error": str(exc),
            }
        rows.append(row)
        if row["status"] != "PASS":
            failures.append(row)
        print(
            "[scbs55-online-probe] {status} key={key} old_count={old_count} expected={expected}".format(
                status=row["status"],
                key=key,
                old_count=row.get("old_count"),
                expected=expected_count,
            ),
            flush=True,
        )

    result = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "checked_count": len(rows),
        "failure_count": len(failures),
        "failures": failures,
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"SCBS55_USER_ACCEPTANCE_ONLINE_PROBE={result['status']} output={OUTPUT}")
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
