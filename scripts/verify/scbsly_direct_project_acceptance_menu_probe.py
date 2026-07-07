#!/usr/bin/env python3
"""Probe SCBSLY direct-project acceptance menu visibility and list counts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

import requests


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/migration_alignment/scbs55_user_acceptance_asset_freeze_v1.json"
OUTPUT = ROOT / "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.json"
OUTPUT_MD = ROOT / "artifacts/migration/scbsly_direct_project_acceptance_menu_probe_v1.md"
BASE_URL = os.getenv("SCBSLY_BASE_URL", "https://www.builderp.cn/SCBSLY_V2").rstrip("/")
USERNAME = os.getenv("SCBSLY_USERNAME") or os.getenv("OLD_SCBS_USERNAME")
PASSWORD = os.getenv("SCBSLY_PASSWORD") or os.getenv("OLD_SCBS_PASSWORD")
MENU_ALIASES = {
    "成本统计表（数据）": ["成本统计表（综合）"],
}
PREFERRED_CONFIG_IDS = {
    "租入": "c9fdf7867d9a4509a9b19255741fe9de",
    "还租": "fa1a970eae754b78a7f095606d906b87",
}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def md5(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def config_id_from_link(link: str) -> str:
    query = parse_qs(urlparse(link).query)
    values = query.get("ConfigId") or query.get("configId") or query.get("configid") or []
    return clean(values[0]) if values else ""


def route_kind(link: str) -> str:
    text = clean(link)
    if "LowCode/Form/FormList" in text:
        return "lowcode_form_list"
    if "LowCode/Report/ReportForm" in text:
        return "lowcode_report"
    if text:
        return "custom_route"
    return "menu_group"


def login(session: requests.Session) -> dict[str, Any]:
    if not USERNAME or not PASSWORD:
        raise RuntimeError("SCBSLY_USERNAME/SCBSLY_PASSWORD or OLD_SCBS_USERNAME/OLD_SCBS_PASSWORD are required")
    payload = {
        "Type": "Common",
        "Param": {
            "UserName": USERNAME,
            "IsEncrypt": False,
            "Password": PASSWORD,
            "PasswordMd5": md5(PASSWORD),
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
        raise RuntimeError(f"SCBSLY login failed: {body.get('Code')} {body.get('Msg')}")
    return body["Data"]


def api_get(session: requests.Session, token: str, path: str) -> dict[str, Any]:
    response = session.get(f"{BASE_URL}/api/{path}", headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"GET {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def api_post(session: requests.Session, token: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = session.post(f"{BASE_URL}/api/{path}", json=payload, headers={"Token": token}, timeout=120)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError(f"POST {path} failed: {body.get('Code')} {body.get('Msg')}")
    return body


def enclosure_ident(detail: dict[str, Any]) -> str:
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or []
    fields: list[str] = []
    for column in columns:
        info = column.get("Info") or {}
        field = clean(info.get("Field"))
        if field and clean(info.get("Format")).lower() == "enclosure":
            fields.append(field)
    return ",".join(fields) + ("," if fields else "")


def list_payload(config: dict[str, Any]) -> tuple[str, dict[str, Any], str]:
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
    path = "LowCode/FormApi/ListByTableName"
    policy = "detail_config_without_probe_injected_djzt"
    if other.get("ListApi"):
        path = str(other["ListApi"]).removeprefix("/api/")
        policy = "detail_config_list_api"
    elif other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        path = "LowCode/FormApi/ListByProcedure"
        policy = "detail_config_list_procedure"
    if other.get("SelectSQLID"):
        payload["SelectSQLID"] = other.get("SelectSQLID")
    elif other.get("CustomSelectSql"):
        payload["CustomSelectSql"] = other.get("CustomSelectSql")
    if main.get("IsProjectSearch") is False:
        payload["FieldName"].pop("ProjectIdField", None)
    if other.get("ListDisplayType", {}).get("FromTableShow"):
        payload["ListDisplayType"] = other.get("ListDisplayType")
    return path, payload, policy


def labels_from_manifest() -> list[dict[str, str]]:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    groups = payload.get("user_acceptance_groups") if isinstance(payload.get("user_acceptance_groups"), list) else []
    target = next((group for group in groups if group.get("group_id") == "scbsly_direct_project_business_menus"), None)
    if not isinstance(target, dict):
        raise RuntimeError("missing scbsly_direct_project_business_menus group in manifest")
    rows: list[dict[str, str]] = []
    for category in target.get("categories", []):
        if not isinstance(category, dict):
            continue
        category_name = clean(category.get("name"))
        for label in category.get("items", []):
            rows.append({"category": category_name, "label": clean(label)})
    return rows


def menu_names(menu: dict[str, Any]) -> set[str]:
    return {clean(menu.get("MENU_NAME")), clean(menu.get("DEFAULT_NAME"))} - {""}


def score_menu(label: str, menu: dict[str, Any]) -> tuple[int, int, int, str]:
    names = menu_names(menu)
    link = clean(menu.get("LINK_URL"))
    score = 0
    kind = route_kind(link)
    if kind == "lowcode_form_list":
        score += 100
    elif kind == "lowcode_report":
        score += 80
    elif kind == "custom_route":
        score += 40
    if clean(menu.get("MENU_NAME")) == label:
        score += 50
    if clean(menu.get("DEFAULT_NAME")) == label:
        score += 40
    config_id = config_id_from_link(link)
    if config_id == PREFERRED_CONFIG_IDS.get(label):
        score += 1000
    if config_id:
        score += 5
    return (score, 1 if label in names else 0, 1 if link else 0, link)


def find_candidates(label: str, menus: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    labels = [label, *MENU_ALIASES.get(label, [])]
    for index, candidate_label in enumerate(labels):
        exact = [menu for menu in menus if candidate_label in menu_names(menu)]
        if exact:
            return ("exact" if index == 0 else "alias", sorted(exact, key=lambda menu: score_menu(candidate_label, menu), reverse=True))
    contains = [
        menu
        for menu in menus
        if any(candidate_label in clean(menu.get("MENU_NAME")) or candidate_label in clean(menu.get("DEFAULT_NAME")) for candidate_label in labels)
    ]
    return ("contains", sorted(contains, key=lambda menu: score_menu(label, menu), reverse=True))


def probe_count(session: requests.Session, token: str, config_id: str, kind: str) -> dict[str, Any]:
    if not config_id:
        return {"status": "SKIP", "reason": "missing_config_id"}
    if kind != "lowcode_form_list":
        return {"status": "SKIP", "reason": f"unsupported_route_kind:{kind}", "config_id": config_id}
    config = api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")["Data"]
    path, payload, policy = list_payload(config)
    body = api_post(session, token, path, payload)
    return {
        "status": "PASS",
        "config_id": config_id,
        "api": path,
        "payload_policy": policy,
        "data_count": int(body.get("DataCount") or 0),
    }


def markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# SCBSLY Direct Project Acceptance Menu Probe v1",
        "",
        f"Status: `{payload['status']}`",
        f"Source: `{payload['source_system']}`",
        f"Historical User: `{payload['old_user'].get('UserName')}` / `{payload['old_user'].get('PersonName')}`",
        f"Generated At: `{payload['generated_at']}`",
        "",
        "| 分类 | 菜单 | 匹配方式 | 历史来源显示 | 路由类型 | ConfigId | DataCount | 状态 |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for row in payload["rows"]:
        count = row["count_probe"].get("data_count")
        lines.append(
            "| {category} | {label} | {match_mode} | {matched_menu_name} | {route_kind} | `{config_id}` | {count} | {status} |".format(
                **row,
                count="" if count is None else count,
            )
        )
    lines.extend(["", "## Failures", "", "```json", json.dumps(payload["failures"], ensure_ascii=False, indent=2), "```", ""])
    return "\n".join(lines)


def main() -> int:
    session = requests.Session()
    user = login(session)
    token = user["Token"]
    home = api_post(session, token, "HomeApi/GetCommonHomeInfo", {})
    menus = home.get("Data", {}).get("MenuInfoArr") or []
    if not isinstance(menus, list):
        raise RuntimeError("HomeApi.GetCommonHomeInfo did not return MenuInfoArr[]")

    rows: list[dict[str, Any]] = []
    for item in labels_from_manifest():
        label = item["label"]
        match_mode, candidates = find_candidates(label, menus)
        best = candidates[0] if candidates else {}
        link = clean(best.get("LINK_URL")) if best else ""
        config_id = config_id_from_link(link)
        kind = route_kind(link)
        count_probe: dict[str, Any]
        try:
            count_probe = probe_count(session, token, config_id, kind) if best else {"status": "FAIL", "reason": "menu_not_visible"}
        except Exception as exc:  # noqa: BLE001
            count_probe = {"status": "FAIL", "reason": str(exc), "config_id": config_id}
        status = "PASS" if best and count_probe.get("status") in {"PASS", "SKIP"} else "FAIL"
        rows.append(
            {
                "category": item["category"],
                "label": label,
                "status": status,
                "match_mode": match_mode if best else "missing",
                "matched_menu_name": clean(best.get("MENU_NAME")) if best else "",
                "matched_default_name": clean(best.get("DEFAULT_NAME")) if best else "",
                "candidate_count": len(candidates),
                "route_kind": kind,
                "link_url": link,
                "config_id": config_id,
                "count_probe": count_probe,
            }
        )
        print(
            "[scbsly-direct-menu] {status} {label} match={match} route={route} count={count}".format(
                status=status,
                label=label,
                match=match_mode if best else "missing",
                route=kind,
                count=count_probe.get("data_count", ""),
            ),
            flush=True,
        )

    failures = [row for row in rows if row["status"] != "PASS"]
    payload = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_system": BASE_URL,
        "manifest": str(MANIFEST.relative_to(ROOT)),
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "old_menu_count": len(menus),
        "checked_count": len(rows),
        "pass_count": len([row for row in rows if row["status"] == "PASS"]),
        "failure_count": len(failures),
        "form_list_count_probe_count": len([row for row in rows if row["count_probe"].get("status") == "PASS"]),
        "unsupported_route_count": len([row for row in rows if row["count_probe"].get("status") == "SKIP"]),
        "aliases": MENU_ALIASES,
        "failures": failures,
        "rows": rows,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(markdown(payload), encoding="utf-8")
    print(f"SCBSLY_DIRECT_PROJECT_ACCEPTANCE_MENU_PROBE={payload['status']} output={OUTPUT}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())
