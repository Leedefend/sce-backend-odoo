# -*- coding: utf-8 -*-
"""Incrementally align SCBSLY direct-project acceptance facts to the live old system.

Run through ``odoo shell``. Unlike the frozen full replay, this script keeps the
existing carrier rows intact and only reconciles rows that are newly visible in
the live old system.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(os.getenv("MIGRATION_REPO_ROOT", "/mnt"))
if not (ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json").exists():
    ROOT = Path.cwd()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.verify.online_capture_security import require_online_capture  # noqa: E402

IDENTITY_LOCK = Path(
    os.getenv("MIGRATION_SCBSLY_IDENTITY_LOCK")
    or ROOT / "artifacts/migration/scbsly_direct_project_old_identity_lock_v1.json"
)
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(ROOT / "artifacts/migration")))
OUTPUT_JSON = ARTIFACT_ROOT / "scbsly_direct_project_current_online_incremental_replay_result_v1.json"
SOURCE_SYSTEM = "online_old_scbsly"
BASE_URL = os.getenv("SCBSLY_BASE_URL", "").rstrip("/")
USERNAME = os.getenv("SCBSLY_USERNAME")
PASSWORD = os.getenv("SCBSLY_PASSWORD")
ROWINDEX_HEAD_REPLACEMENT_LABELS = {"入库", "零星用工", "机械台班记录", "进项上报"}
REQUEST_TIMEOUT = (8, 30)


def clean(value):
    return re.sub(r"\s+", " ", str(value or "").strip())


def md5(value):
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, payload):
    target = path
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except PermissionError:
        target = Path("/tmp") / path.name
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    payload["output_json"] = str(target)
    return target


def ensure_allowed_db():
    allowlist = {
        item.strip()
        for item in os.getenv("MIGRATION_REPLAY_DB_ALLOWLIST", "sc_odoo,sc_demo").split(",")
        if item.strip()
    }
    if env.cr.dbname not in allowlist:  # noqa: F821
        raise RuntimeError({"db_name_not_allowed_for_replay": env.cr.dbname, "allowlist": sorted(allowlist)})  # noqa: F821


def login(session):
    if not USERNAME or not PASSWORD:
        raise RuntimeError("SCBSLY_USERNAME and SCBSLY_PASSWORD are required")
    response = session.post(
        f"{BASE_URL}/api/System/UserApi/Login",
        json={
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
        },
        timeout=60,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000" or not body.get("Data", {}).get("Token"):
        raise RuntimeError({"scbsly_login_failed": body.get("Code"), "message": body.get("Msg")})
    return body["Data"]


def api_get(session, token, path):
    response = session.get(f"{BASE_URL}/api/{path}", headers={"Token": token}, timeout=60)
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"api_get_failed": path, "code": body.get("Code"), "message": body.get("Msg")})
    return body


def api_post(session, token, path, payload):
    response = session.post(
        f"{BASE_URL}/api/{path}",
        json=payload,
        headers={"Token": token},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    body = response.json()
    if str(body.get("Code")) != "10000":
        raise RuntimeError({"api_post_failed": path, "code": body.get("Code"), "message": body.get("Msg")})
    return body


def enclosure_ident(detail):
    columns = detail.get("ContentTable", {}).get("TableConfig", {}).get("ColumnConfig") or []
    fields = []
    for column in columns:
        info = column.get("Info") or {}
        field = clean(info.get("Field"))
        if field and clean(info.get("Format")).lower() == "enclosure":
            fields.append(field)
    return ",".join(fields) + ("," if fields else "")


def list_payload(config):
    detail = json.loads(config.get("DETAIL_CONFIG") or "{}")
    other = detail.get("OtherConfig") if isinstance(detail.get("OtherConfig"), dict) else {}
    main = other.get("MainTable") if isinstance(other.get("MainTable"), dict) else {}
    where = deepcopy(detail.get("WhereInfo") if isinstance(detail.get("WhereInfo"), dict) else {})
    payload = {
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
    if other.get("ListApi"):
        path = str(other["ListApi"]).removeprefix("/api/")
    elif other.get("ListProcedure"):
        payload["Procedure"] = other["ListProcedure"]
        path = "LowCode/FormApi/ListByProcedure"
    if other.get("SelectSQLID"):
        payload["SelectSQLID"] = other.get("SelectSQLID")
    elif other.get("CustomSelectSql"):
        payload["CustomSelectSql"] = other.get("CustomSelectSql")
    if main.get("IsProjectSearch") is False:
        payload["FieldName"].pop("ProjectIdField", None)
    if other.get("ListDisplayType", {}).get("FromTableShow"):
        payload["ListDisplayType"] = other.get("ListDisplayType")
    return path, payload


def rows_from_body(body):
    data = body.get("Data")
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("List", "Rows", "Data", "list", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def row_hash(row):
    return hashlib.sha256(json.dumps(row, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def identity_value(row, identity_field):
    fields = []
    if identity_field:
        fields.append(identity_field)
    fields.extend(["Id", "id", "ID", "DJBH", "PID", "Pid", "pid", "RowIndex"])
    seen = set()
    for field in fields:
        if field in seen:
            continue
        seen.add(field)
        value = clean(row.get(field))
        if value:
            return value
    return "hash:" + row_hash(row)


def specs_from_identity_lock():
    return [
        {
            "label": row.get("label"),
            "category": row.get("category"),
            "config_id": row.get("config_id"),
            "identity_field": row.get("identity_field"),
        }
        for row in load_json(IDENTITY_LOCK).get("rows") or []
        if row.get("label") and row.get("config_id")
    ]


def fetch_config(session, token, config_id):
    return api_get(session, token, f"LowCode/FormApi/GetConfigById?Id={config_id}&LoadInitData=true")["Data"]


def fetch_page(session, token, path, payload, page):
    payload["PageIndex"] = page
    payload["PageSize"] = 1
    rows = rows_from_body(api_post(session, token, path, payload))
    if not rows:
        raise RuntimeError({"empty_scbsly_page": page})
    return rows[0]


def active_ids_by_label(model, label):
    rows = model.search_read(
        [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)],
        ["legacy_record_id"],
    )
    return {clean(row.get("legacy_record_id")) for row in rows if clean(row.get("legacy_record_id"))}


def main():
    require_online_capture(("scbsly",))
    ensure_allowed_db()
    replay_source = ROOT / "scripts/migration/scbsly_direct_project_direct_acceptance_replay.py"
    namespace = globals()
    namespace["__name__"] = "__scbsly_direct_incremental_helper__"
    incremental_output_json = OUTPUT_JSON
    exec(replay_source.read_text(encoding="utf-8").split("\ndef main():", 1)[0], namespace)
    namespace["OUTPUT_JSON"] = incremental_output_json

    session = requests.Session()
    user = login(session)
    token = user["Token"]
    Model = env["sc.legacy.direct.acceptance.fact"].sudo().with_context(active_test=False)  # noqa: F821
    project_cache = {}
    results = []

    for spec in specs_from_identity_lock():
        label = spec["label"]
        config = fetch_config(session, token, spec["config_id"])
        path, payload = list_payload(config)
        count_body = api_post(session, token, path, {**payload, "PageIndex": 1, "PageSize": 1})
        online_count = int(count_body.get("DataCount") or 0)
        existing_ids = active_ids_by_label(Model, label)
        existing_count = len(existing_ids)
        pages = []
        deactivate_ids = []
        deactivate_head_row_index_zero = False
        if online_count > existing_count:
            if spec["identity_field"] == "RowIndex" and label in ROWINDEX_HEAD_REPLACEMENT_LABELS:
                pages = [1, *range(existing_count + 1, online_count + 1)]
                deactivate_ids = ["1"]
                deactivate_head_row_index_zero = True
            else:
                pages = list(range(1, online_count - existing_count + 1))

        created = updated = deactivated = 0
        fetched = []
        errors = []
        for legacy_id in deactivate_ids:
            recs = Model.search(
                [
                    ("source_system", "=", SOURCE_SYSTEM),
                    ("acceptance_label", "=", label),
                    ("legacy_record_id", "=", legacy_id),
                    ("active", "=", True),
                ]
            )
            if recs:
                recs.write({"active": False})
                deactivated += len(recs)
        if deactivate_head_row_index_zero:
            recs = Model.search(
                [
                    ("source_system", "=", SOURCE_SYSTEM),
                    ("acceptance_label", "=", label),
                    ("row_index", "=", 0),
                    ("active", "=", True),
                ]
            )
            if recs:
                recs.write({"active": False})
                deactivated += len(recs)

        seen = set()
        for page in pages:
            try:
                row = fetch_page(session, token, path, payload, page)
                values = namespace["values_for"](row, spec, project_cache)
                legacy_id = values["legacy_record_id"]
                if legacy_id in seen:
                    raise RuntimeError({"duplicate_fetched_identity": legacy_id, "page": page})
                seen.add(legacy_id)
                existing = Model.search(
                    [
                        ("source_system", "=", SOURCE_SYSTEM),
                        ("acceptance_label", "=", label),
                        ("legacy_record_id", "=", legacy_id),
                    ],
                    limit=1,
                )
                if existing:
                    existing.write(values)
                    updated += 1
                else:
                    Model.create(values)
                    created += 1
                fetched.append({"page": page, "legacy_record_id": legacy_id})
            except Exception as exc:  # noqa: BLE001
                errors.append({"page": page, "error": repr(exc)})

        active_after = Model.search_count(
            [("source_system", "=", SOURCE_SYSTEM), ("acceptance_label", "=", label), ("active", "=", True)]
        )
        status = "PASS" if not errors and active_after == online_count else "FAIL"
        results.append(
            {
                "label": label,
                "category": spec.get("category"),
                "config_id": spec.get("config_id"),
                "identity_field": spec.get("identity_field"),
                "online_count": online_count,
                "active_before": existing_count,
                "active_after": active_after,
                "created": created,
                "updated": updated,
                "deactivated": deactivated,
                "fetched": fetched,
                "errors": errors,
                "status": status,
            }
        )

    env.cr.commit()  # noqa: F821
    failures = [row for row in results if row["status"] != "PASS"]
    summary = {
        "status": "PASS" if not failures else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_name": env.cr.dbname,  # noqa: F821
        "source_system": BASE_URL,
        "old_user": {
            key: user.get(key)
            for key in ("UserId", "UserName", "PersonName", "ProjectId", "ProjectName", "CompanyId", "CompanyName")
        },
        "checked_count": len(results),
        "failure_count": len(failures),
        "created_total": sum(row["created"] for row in results),
        "updated_total": sum(row["updated"] for row in results),
        "deactivated_total": sum(row["deactivated"] for row in results),
        "failures": failures,
        "rows": results,
    }
    output = write_json(OUTPUT_JSON, summary)
    print(json.dumps({"output_json": str(output), **summary}, ensure_ascii=False, indent=2, sort_keys=True))
    if failures:
        raise RuntimeError(summary)


main()
