#!/usr/bin/env python3
"""Generate XML assets for legacy workflow approval audit facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_workflow_audit_sc_v1")
XML_REL_PATH = Path("30_relation/legacy_workflow_audit/legacy_workflow_audit_v1.xml")
EXTERNAL_REL_PATH = Path("manifest/legacy_workflow_audit_external_id_manifest_v1.json")
VALIDATION_REL_PATH = Path("manifest/legacy_workflow_audit_validation_manifest_v1.json")
ASSET_MANIFEST_REL_PATH = Path("manifest/legacy_workflow_audit_asset_manifest_v1.json")
CATALOG_REL_PATH = Path("manifest/migration_asset_catalog_v1.json")
ASSET_PACKAGE_ID = "legacy_workflow_audit_sc_v1"
GENERATED_AT = "2026-04-15T16:10:00+00:00"
EXPECTED_RAW_ROWS = 163245
EXPECTED_LOADABLE_ROWS = 79702

TARGET_SPECS = [
    ("project", "BASE_SYSTEM_PROJECT", "project.project", "manifest/project_external_id_manifest_v1.json", ["legacy_key", "target_lookup.value"]),
    ("contract", "T_ProjectContract_Out", "construction.contract", "manifest/contract_external_id_manifest_v1.json", ["legacy_contract_id"]),
    ("receipt", "C_JFHKLR", "payment.request", "manifest/receipt_external_id_manifest_v1.json", ["legacy_receipt_id"]),
    ("outflow_request", "C_ZFSQGL", "payment.request", "manifest/outflow_request_external_id_manifest_v1.json", ["legacy_outflow_id"]),
    ("actual_outflow", "T_FK_Supplier", "payment.request", "manifest/actual_outflow_external_id_manifest_v1.json", ["legacy_actual_outflow_id"]),
    ("supplier_contract", "T_GYSHT_INFO", "construction.contract", "manifest/supplier_contract_external_id_manifest_v1.json", ["legacy_supplier_contract_id"]),
    ("outflow_request_line", "C_ZFSQGL_CB", "payment.request.line", "manifest/outflow_request_line_external_id_manifest_v1.json", ["legacy_outflow_line_id"]),
    ("receipt_invoice_line", "C_JFHKLR_CB", "sc.receipt.invoice.line", "manifest/receipt_invoice_line_external_id_manifest_v1.json", ["legacy_receipt_invoice_line_id", "attachment_candidate_keys.Id"]),
]

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), a.Id) AS Id,
  CONVERT(nvarchar(max), a.SJBMC) AS SJBMC,
  CONVERT(nvarchar(max), a.DJID) AS DJID,
  CONVERT(nvarchar(max), a.business_Id) AS business_Id,
  CONVERT(nvarchar(max), a.f_SPZT) AS f_SPZT,
  CONVERT(nvarchar(max), a.f_Back_YJLX) AS f_Back_YJLX,
  CONVERT(nvarchar(max), a.f_SPYJ) AS f_SPYJ,
  CONVERT(nvarchar(max), a.f_LRRId) AS f_LRRId,
  CONVERT(nvarchar(max), a.f_LRR) AS f_LRR,
  CONVERT(nvarchar(max), a.f_SPSJ, 120) AS f_SPSJ,
  CONVERT(nvarchar(max), a.RecevieTime, 120) AS RecevieTime,
  CONVERT(nvarchar(max), a.pid) AS pid,
  CONVERT(nvarchar(max), a.SPLX) AS SPLX,
  CONVERT(nvarchar(max), a.S_Execute_DetailStatus_Id) AS S_Execute_DetailStatus_Id,
  CONVERT(nvarchar(max), a.S_Execute_Detail_Step_Id) AS S_Execute_Detail_Step_Id,
  CONVERT(nvarchar(max), a.S_Setup_Step_Id) AS S_Setup_Step_Id,
  CONVERT(nvarchar(max), a.S_Setup_Template_Id) AS S_Setup_Template_Id,
  CONVERT(nvarchar(max), st.f_BZMC) AS setup_step_name,
  CONVERT(nvarchar(max), tm.f_MBMC) AS template_name,
  CONVERT(nvarchar(max), tm.f_S_setup_business_Name) AS template_business_name
FROM dbo.S_Execute_Approval a
LEFT JOIN dbo.S_Setup_Step st ON a.S_Setup_Step_Id = st.Id
LEFT JOIN dbo.S_Setup_Template tm ON a.S_Setup_Template_Id = tm.Id
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SJBMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(business_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_Back_YJLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPYJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRRId, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_LRR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_SPSJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(RecevieTime, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SPLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(S_Execute_DetailStatus_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(S_Execute_Detail_Step_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(S_Setup_Step_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(S_Setup_Template_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(setup_step_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(template_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(template_business_name, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id",
    "SJBMC",
    "DJID",
    "business_Id",
    "f_SPZT",
    "f_Back_YJLX",
    "f_SPYJ",
    "f_LRRId",
    "f_LRR",
    "f_SPSJ",
    "RecevieTime",
    "pid",
    "SPLX",
    "S_Execute_DetailStatus_Id",
    "S_Execute_Detail_Step_Id",
    "S_Setup_Step_Id",
    "S_Setup_Template_Id",
    "setup_step_name",
    "template_name",
    "template_business_name",
]


class WorkflowAuditAssetError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise WorkflowAuditAssetError(message)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def deep_get(row: dict[str, Any], path: str) -> str:
    value: Any = row
    for part in path.split("."):
        if not isinstance(value, dict):
            return ""
        value = value.get(part)
    return clean(value)


def safe_external_suffix(value: str) -> str:
    suffix = re.sub(r"[^0-9A-Za-z_]+", "_", value).strip("_").lower()
    require(bool(suffix), "cannot build external id from blank workflow id")
    return suffix


def normalize_source_table(value: str) -> str:
    text = clean(value)
    aliases = {
        "T_ProjectContract_OutInfo": "T_ProjectContract_Out",
        "ProjectContract_Out": "T_ProjectContract_Out",
        "C_JFHKLR_CB_FP": "C_JFHKLR_CB",
    }
    return aliases.get(text, text)


def workflow_action(row: dict[str, str]) -> str:
    status = clean(row.get("f_SPZT"))
    back_type = clean(row.get("f_Back_YJLX"))
    if back_type and back_type not in {"0", "-1"}:
        return "reject_or_back"
    if status in {"1", "2", "3"}:
        return "approve"
    if status in {"-1", "4", "5"}:
        return "reject_or_cancel"
    return "unknown"


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0",
    ]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sql_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != len(SQL_COLUMNS):
            continue
        rows.append(dict(zip(SQL_COLUMNS, parts)))
    require(len(rows) == EXPECTED_RAW_ROWS, f"workflow raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return rows


def build_target_index(asset_root: Path) -> tuple[dict[tuple[str, str], list[dict[str, str]]], dict[str, list[dict[str, str]]]]:
    source_index: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    any_index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for lane, source_table, target_model, rel_path, key_paths in TARGET_SPECS:
        manifest = load_json(asset_root / rel_path)
        for row in manifest.get("records", []):
            if row.get("status") != "loadable":
                continue
            external_id = clean(row.get("external_id"))
            if not external_id:
                continue
            for key_path in key_paths:
                value = deep_get(row, key_path)
                if not value:
                    continue
                item = {
                    "lane": lane,
                    "source_table": source_table,
                    "target_model": target_model,
                    "external_id": external_id,
                    "key_path": key_path,
                }
                source_index[(source_table, value)].append(item)
                any_index[value].append(item)
    require(source_index, "target source index is empty")
    require(any_index, "target any-index is empty")
    return source_index, any_index


def add_text_field(record: ET.Element, name: str, value: object, *, required: bool = False) -> None:
    text = clean(value)
    if not text and not required:
        return
    field = ET.SubElement(record, "field", {"name": name})
    field.text = text


def write_xml(path: Path, records: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    root = ET.Element("odoo")
    data = ET.SubElement(root, "data", {"noupdate": "1"})
    for row in records:
        record = ET.SubElement(data, "record", {"id": row["external_id"], "model": "sc.legacy.workflow.audit"})
        add_text_field(record, "legacy_workflow_id", row["legacy_workflow_id"], required=True)
        add_text_field(record, "legacy_pid", row["legacy_pid"])
        add_text_field(record, "legacy_djid", row["legacy_djid"], required=True)
        add_text_field(record, "legacy_business_id", row["legacy_business_id"])
        add_text_field(record, "legacy_source_table", row["legacy_source_table"])
        add_text_field(record, "legacy_detail_status_id", row["legacy_detail_status_id"])
        add_text_field(record, "legacy_detail_step_id", row["legacy_detail_step_id"])
        add_text_field(record, "legacy_setup_step_id", row["legacy_setup_step_id"])
        add_text_field(record, "legacy_template_id", row["legacy_template_id"])
        add_text_field(record, "legacy_step_name", row["legacy_step_name"])
        add_text_field(record, "legacy_template_name", row["legacy_template_name"])
        add_text_field(record, "target_model", row["target_model"], required=True)
        add_text_field(record, "target_external_id", row["target_external_id"], required=True)
        add_text_field(record, "target_lane", row["target_lane"], required=True)
        add_text_field(record, "actor_legacy_user_id", row["actor_legacy_user_id"])
        add_text_field(record, "actor_name", row["actor_name"])
        add_text_field(record, "approved_at", row["approved_at"])
        add_text_field(record, "received_at", row["received_at"])
        add_text_field(record, "approval_note", row["approval_note"])
        add_text_field(record, "action_classification", row["action_classification"], required=True)
        add_text_field(record, "legacy_status", row["legacy_status"])
        add_text_field(record, "legacy_back_type", row["legacy_back_type"])
        add_text_field(record, "legacy_approval_type", row["legacy_approval_type"])
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def update_catalog(asset_root: Path, manifest_hash: str) -> None:
    catalog_path = asset_root / CATALOG_REL_PATH
    catalog = load_json(catalog_path)
    package = {
        "asset_manifest_path": str(ASSET_MANIFEST_REL_PATH),
        "asset_manifest_sha256": manifest_hash,
        "asset_package_id": ASSET_PACKAGE_ID,
        "baseline_package": True,
        "business_priority": "legacy_workflow_audit_fact",
        "dependencies": [
            "contract_sc_v1",
            "receipt_sc_v1",
            "outflow_request_sc_v1",
            "actual_outflow_sc_v1",
            "supplier_contract_sc_v1",
        ],
        "layer": "30_relation",
        "load_phase": 30,
        "package_type": "historical_workflow_audit_fact",
        "required": True,
        "risk_class": "historical_audit_fact",
        "target_model": "sc.legacy.workflow.audit",
        "verification_command": "python3 scripts/migration/legacy_workflow_audit_asset_verify.py --asset-root migration_assets --lane legacy_workflow_audit --check",
    }
    catalog["package_order"] = [item for item in catalog.get("package_order", []) if item != ASSET_PACKAGE_ID]
    catalog["package_order"].append(ASSET_PACKAGE_ID)
    catalog["packages"] = [item for item in catalog.get("packages", []) if item.get("asset_package_id") != ASSET_PACKAGE_ID]
    catalog["packages"].append(package)
    catalog["generated_at"] = GENERATED_AT
    write_json(catalog_path, catalog)


def build_records(asset_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    source_rows = parse_sql_rows(run_sql())
    source_index, any_index = build_target_index(asset_root)
    records: list[dict[str, str]] = []
    blocked: list[dict[str, str]] = []
    counters: Counter[str] = Counter()
    lane_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    external_ids: Counter[str] = Counter()
    matched_targets: set[str] = set()

    for row in source_rows:
        source_table = normalize_source_table(row.get("SJBMC", ""))
        djid = clean(row.get("DJID"))
        business_id = clean(row.get("business_Id"))
        action = workflow_action(row)
        action_counts[action] += 1

        matches: list[dict[str, str]] = []
        match_key = ""
        if djid:
            matches = any_index.get(djid, [])
            match_key = "DJID"
        if not matches and source_table and business_id:
            matches = source_index.get((source_table, business_id), [])
            match_key = "SJBMC_business_Id"
        if not matches and business_id:
            matches = any_index.get(business_id, [])
            match_key = "business_Id_any"
        if not matches:
            counters["blocked_target_not_assetized_or_not_loadable"] += 1
            blocked.append({"legacy_workflow_id": clean(row.get("Id")), "reason": "target_not_assetized_or_not_loadable"})
            continue
        targets = {match["external_id"] for match in matches}
        if len(targets) > 1:
            counters["blocked_ambiguous_target"] += 1
            blocked.append({"legacy_workflow_id": clean(row.get("Id")), "reason": "ambiguous_target"})
            continue
        match = matches[0]
        external_id = "legacy_workflow_audit_sc_%s" % safe_external_suffix(clean(row.get("Id")))
        external_ids[external_id] += 1
        lane_counts[match["lane"]] += 1
        matched_targets.add("%s:%s" % (match["lane"], match["external_id"]))
        records.append(
            {
                "external_id": external_id,
                "legacy_workflow_id": clean(row.get("Id")),
                "legacy_pid": clean(row.get("pid")),
                "legacy_djid": djid,
                "legacy_business_id": business_id,
                "legacy_source_table": source_table,
                "legacy_detail_status_id": clean(row.get("S_Execute_DetailStatus_Id")),
                "legacy_detail_step_id": clean(row.get("S_Execute_Detail_Step_Id")),
                "legacy_setup_step_id": clean(row.get("S_Setup_Step_Id")),
                "legacy_template_id": clean(row.get("S_Setup_Template_Id")),
                "legacy_step_name": clean(row.get("setup_step_name")),
                "legacy_template_name": clean(row.get("template_name")) or clean(row.get("template_business_name")),
                "target_model": match["target_model"],
                "target_external_id": match["external_id"],
                "target_lane": match["lane"],
                "actor_legacy_user_id": clean(row.get("f_LRRId")),
                "actor_name": clean(row.get("f_LRR")),
                "approved_at": clean(row.get("f_SPSJ")),
                "received_at": clean(row.get("RecevieTime")),
                "approval_note": clean(row.get("f_SPYJ")),
                "action_classification": action,
                "legacy_status": clean(row.get("f_SPZT")),
                "legacy_back_type": clean(row.get("f_Back_YJLX")),
                "legacy_approval_type": clean(row.get("SPLX")),
                "match_key": match_key,
            }
        )

    require(len(records) == EXPECTED_LOADABLE_ROWS, f"loadable row count drifted: {len(records)} != {EXPECTED_LOADABLE_ROWS}")
    duplicate_ids = [key for key, count in external_ids.items() if count > 1]
    require(not duplicate_ids, f"duplicate workflow audit external ids: {duplicate_ids[:5]}")
    return records, {
        "raw_rows": len(source_rows),
        "loadable_records": len(records),
        "blocked_records": len(source_rows) - len(records),
        "blocked_reason_counts": dict(sorted(counters.items())),
        "lane_counts": dict(sorted(lane_counts.items())),
        "action_counts": dict(sorted(action_counts.items())),
        "matched_target_records": len(matched_targets),
        "blocked_samples": blocked[:50],
    }


def generate(asset_root: Path, runtime_root: Path) -> dict[str, Any]:
    records, summary = build_records(asset_root)
    xml_path = asset_root / XML_REL_PATH
    external_path = asset_root / EXTERNAL_REL_PATH
    validation_path = asset_root / VALIDATION_REL_PATH
    asset_manifest_path = asset_root / ASSET_MANIFEST_REL_PATH

    write_xml(xml_path, records)
    external_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "external_id_rule": "legacy_workflow_audit_sc_<S_Execute_Approval.Id>",
        "lane_id": "legacy_workflow_audit",
        "records": [
            {
                "external_id": row["external_id"],
                "legacy_workflow_id": row["legacy_workflow_id"],
                "legacy_djid": row["legacy_djid"],
                "target_external_id": row["target_external_id"],
                "target_lane": row["target_lane"],
                "target_model": row["target_model"],
                "status": "loadable",
            }
            for row in records
        ],
        "summary": {
            "loadable": len(records),
            "blocked": summary["blocked_records"],
            "raw_rows": summary["raw_rows"],
        },
    }
    write_json(external_path, external_manifest)
    validation_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "business_boundary": {
            "historical_approval_audit_fact": "included",
            "tier_review": "excluded",
            "tier_definition": "excluded",
            "runtime_workflow_state": "excluded",
            "target_business_state_mutation": "excluded",
        },
        "counts": summary,
        "validation_gates": {
            "generate_time": [
                "legacy_workflow_id_unique",
                "target_external_id_resolves_to_asset_manifest",
                "no_tier_review_records_generated",
                "no_tier_definition_records_generated",
                "no_runtime_workflow_records_generated",
                "no_database_integer_ids_required",
            ]
        },
    }
    write_json(validation_path, validation_manifest)
    asset_manifest = {
        "asset_manifest_version": "1.0",
        "asset_package_id": ASSET_PACKAGE_ID,
        "assets": [
            {"path": str(XML_REL_PATH), "sha256": sha256_file(xml_path), "type": "xml"},
            {"path": str(EXTERNAL_REL_PATH), "sha256": sha256_file(external_path), "type": "external_id_manifest"},
            {"path": str(VALIDATION_REL_PATH), "sha256": sha256_file(validation_path), "type": "validation_manifest"},
        ],
        "baseline_package": True,
        "counts": summary,
        "db_writes": 0,
        "dependencies": ["contract_sc_v1", "receipt_sc_v1", "outflow_request_sc_v1", "actual_outflow_sc_v1", "supplier_contract_sc_v1"],
        "generated_at": GENERATED_AT,
        "lane": {"lane_id": "legacy_workflow_audit", "layer": "30_relation", "load_phase": 30},
        "odoo_shell": False,
        "source_counts": {
            "source_table": "S_Execute_Approval",
            "raw_rows": summary["raw_rows"],
            "loadable_rows": summary["loadable_records"],
            "blocked_rows": summary["blocked_records"],
        },
        "target": {"model": "sc.legacy.workflow.audit", "source_table": "S_Execute_Approval"},
    }
    write_json(asset_manifest_path, asset_manifest)
    update_catalog(asset_root, sha256_file(asset_manifest_path))
    runtime_payload = {
        "status": "PASS",
        "asset_package_id": ASSET_PACKAGE_ID,
        "xml_path": str(xml_path),
        "asset_manifest_path": str(asset_manifest_path),
        "counts": summary,
        "db_writes": 0,
        "odoo_shell": False,
    }
    write_json(runtime_root / "legacy_workflow_audit_asset_generation_v1.json", runtime_payload)
    return runtime_payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy workflow audit XML assets.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--runtime-root", default=str(RUNTIME_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = generate(Path(args.asset_root), Path(args.runtime_root))
    except (WorkflowAuditAssetError, json.JSONDecodeError, ET.ParseError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_WORKFLOW_AUDIT_ASSET_GENERATE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_WORKFLOW_AUDIT_ASSET_GENERATE=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
