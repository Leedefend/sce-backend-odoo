#!/usr/bin/env python3
"""Generate repository-trackable user XML migration assets without DB writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET


SQLCMD = [
    "docker",
    "exec",
    "legacy-sqlserver",
    "/opt/mssql-tools18/bin/sqlcmd",
    "-S",
    "localhost",
    "-U",
    "sa",
    "-P",
    "ChangeThis_Strong_Password_123!",
    "-C",
    "-d",
    "LegacyDb",
    "-s",
    "\t",
    "-W",
]
ASSET_PACKAGE_ID = "user_sc_v1"
LANE = "user"
LAYER = "10_master"
TARGET_MODEL = "res.users"


class UserAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value)
    return re.sub(r"\s+", " ", text.replace("\u3000", " ").strip())


def require(condition: bool, message: str) -> None:
    if not condition:
        raise UserAssetError(message)


def safe_token(value: str) -> str:
    token = re.sub(r"[^0-9A-Za-z_]+", "_", value.strip())
    token = re.sub(r"_+", "_", token).strip("_")
    return token or "missing"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def run_sql(sql: str) -> list[list[str]]:
    proc = subprocess.run(
        [*SQLCMD, "-h", "-1", "-Q", f"SET NOCOUNT ON; {sql}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[list[str]] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("("):
            continue
        rows.append([part.strip() for part in line.split("\t")])
    return rows


def fetch_users() -> list[dict[str, Any]]:
    rows = run_sql(
        """
        SELECT
          CONVERT(nvarchar(100), ID) AS legacy_user_id,
          CONVERT(nvarchar(100), PID) AS legacy_user_pid,
          CONVERT(nvarchar(200), USERNAME) AS legacy_login,
          CONVERT(nvarchar(200), PERSON_NAME) AS name,
          CONVERT(nvarchar(100), PHONE_NUMBER) AS phone,
          CONVERT(nvarchar(200), EMAIL) AS email,
          CONVERT(nvarchar(20), DEL) AS deleted,
          CONVERT(nvarchar(20), ISADMIN) AS is_admin
        FROM dbo.BASE_SYSTEM_USER
        WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), ID))), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), USERNAME))), '') IS NOT NULL
          AND NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), PERSON_NAME))), '') IS NOT NULL
        ORDER BY PID;
        """
    )
    records = []
    for row in rows:
        legacy_user_id = clean(row[0] if len(row) > 0 else "")
        legacy_user_pid = clean(row[1] if len(row) > 1 else "")
        legacy_login = clean(row[2] if len(row) > 2 else "")
        name = clean(row[3] if len(row) > 3 else "")
        records.append(
            {
                "external_id": f"legacy_user_sc_{safe_token(legacy_user_id)}",
                "legacy_user_id": legacy_user_id,
                "legacy_user_pid": legacy_user_pid,
                "legacy_login": legacy_login,
                "login": f"legacy_{safe_token(legacy_user_id)}",
                "name": name,
                "phone": clean(row[4] if len(row) > 4 else ""),
                "email": clean(row[5] if len(row) > 5 else "").lower(),
                "active": "0" if clean(row[6] if len(row) > 6 else "") == "1" else "1",
                "legacy_is_admin": clean(row[7] if len(row) > 7 else ""),
            }
        )
    return records


def validate(records: list[dict[str, Any]]) -> None:
    require(records, "user records must not be empty")
    external_ids = [record["external_id"] for record in records]
    logins = [record["login"] for record in records]
    legacy_ids = [record["legacy_user_id"] for record in records]
    require(len(external_ids) == len(set(external_ids)), "duplicate external ids")
    require(len(logins) == len(set(logins)), "duplicate generated logins")
    require(len(legacy_ids) == len(set(legacy_ids)), "duplicate legacy user ids")
    for record in records:
        require(record["external_id"].startswith("legacy_user_sc_"), f"invalid external id: {record}")
        require(record["name"], f"missing name: {record}")
        require(record["login"], f"missing login: {record}")


def write_xml(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for record in records:
        element = ET.SubElement(data, "record", {"id": record["external_id"], "model": TARGET_MODEL})
        for field_name in ("name", "login", "active", "email"):
            field = ET.SubElement(element, "field", {"name": field_name})
            field.text = clean(record.get(field_name))
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_package(asset_root: Path, records: list[dict[str, Any]], source: str, asset_version: str) -> dict[str, Any]:
    xml_path = asset_root / LAYER / LANE / "user_master_v1.xml"
    external_path = asset_root / "manifest" / "user_external_id_manifest_v1.json"
    validation_path = asset_root / "manifest" / "user_validation_manifest_v1.json"
    manifest_path = asset_root / "manifest" / "user_asset_manifest_v1.json"
    write_xml(xml_path, records)
    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "summary": {
            "loadable": len(records),
            "discarded": 0,
            "inactive": sum(1 for record in records if record["active"] == "0"),
        },
        "records": [
            {
                "external_id": record["external_id"],
                "legacy_user_id": record["legacy_user_id"],
                "legacy_user_pid": record["legacy_user_pid"],
                "legacy_login": record["legacy_login"],
                "target_model": TARGET_MODEL,
                "target_lookup": {"field": "xml_id", "value": record["external_id"]},
                "status": "loadable",
            }
            for record in records
        ],
    }
    write_json(external_path, external_manifest)
    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "failure_policy": {
            "missing_legacy_user_id": "block_package",
            "missing_login": "block_package",
            "missing_name": "block_package",
            "duplicate_external_id": "block_package",
            "duplicate_generated_login": "block_package",
            "group_assignment_requested": "block_package",
        },
        "validation_gates": {
            "generate_time": [
                "legacy_base_user_exists",
                "legacy_user_id_unique",
                "generated_login_unique",
                "external_id_unique",
                "no_group_assignment",
                "no_role_profile_assignment",
                "no_permission_fabrication",
            ],
            "preload": ["asset_files_exist", "asset_hashes_match", "target_model_available"],
            "postload": ["external_id_resolves", "project_member_user_refs_resolve"],
        },
    }
    write_json(validation_path, validation_manifest)
    manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "db_writes": 0,
        "odoo_shell": False,
        "lane": {
            "lane_id": LANE,
            "layer": LAYER,
            "business_priority": "dependency_master_data",
            "risk_class": "authority_anchor",
        },
        "target": {
            "model": TARGET_MODEL,
            "identity_field": "external_id",
            "load_strategy": "odoo_xml_external_id",
        },
        "source_snapshot": {
            "source_system": source,
            "extract_batch_id": f"user_xml_baseline_{asset_version}",
            "source_tables": ["BASE_SYSTEM_USER"],
        },
        "counts": {
            "raw_rows": len(records),
            "loadable_records": len(records),
            "discarded_records": 0,
            "inactive_records": sum(1 for record in records if record["active"] == "0"),
            "deferred_records": 0,
        },
        "dependencies": [],
        "load_order": ["user_master_xml_v1", "user_external_id_manifest_v1", "user_validation_manifest_v1"],
        "idempotency": {
            "mode": "odoo_xml_external_id",
            "duplicate_policy": "update_existing_same_external_id",
            "conflict_policy": "block_package",
        },
        "authority_policy": {
            "groups_id": "not_assigned",
            "sc_role_profile": "not_assigned",
            "department": "deferred",
            "post": "deferred",
        },
        "validation_gates": validation_manifest["validation_gates"]["generate_time"],
        "assets": [
            {
                "asset_id": "user_master_xml_v1",
                "path": f"{LAYER}/{LANE}/user_master_v1.xml",
                "format": "xml",
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(xml_path),
            },
            {
                "asset_id": "user_external_id_manifest_v1",
                "path": "manifest/user_external_id_manifest_v1.json",
                "format": "json",
                "record_count": len(records),
                "required": True,
                "sha256": sha256_file(external_path),
            },
            {
                "asset_id": "user_validation_manifest_v1",
                "path": "manifest/user_validation_manifest_v1.json",
                "format": "json",
                "record_count": 1,
                "required": True,
                "sha256": sha256_file(validation_path),
            },
        ],
    }
    write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate user XML migration asset package without DB writes.")
    parser.add_argument("--out", default=".runtime_artifacts/migration_assets/user_sc_v1")
    parser.add_argument("--baseline-out", help="Optional repository baseline asset root")
    parser.add_argument("--source", default="sc")
    parser.add_argument("--asset-version", default="v1")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        records = fetch_users()
        validate(records)
        runtime_manifest = write_package(Path(args.out), records, args.source, args.asset_version)
        baseline_manifest = None
        if args.baseline_out:
            baseline_manifest = write_package(Path(args.baseline_out), records, args.source, args.asset_version)
    except (UserAssetError, subprocess.CalledProcessError, OSError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("USER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    payload = {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "runtime_out": args.out,
        "baseline_out": args.baseline_out or "",
        "loadable_records": len(records),
        "inactive_records": runtime_manifest["counts"]["inactive_records"],
        "baseline_asset_manifest_hash": sha256_file(Path(args.baseline_out) / "manifest" / "user_asset_manifest_v1.json") if args.baseline_out else "",
        "db_writes": 0,
        "odoo_shell": False,
    }
    print("USER_ASSET_GENERATOR=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
