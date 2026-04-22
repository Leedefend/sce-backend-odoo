#!/usr/bin/env python3
"""Screen BASE_SYSTEM_FILE attachment linkage across migration asset manifests."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/global_attachment_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_global_attachment_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_global_attachment_screen_v1.md")
EXPECTED_FILE_ROWS = 126967
SOURCE_FIELDS = ("BILLID", "BUSINESSID", "PID")
SOURCE_PID_TABLES = [
    "BASE_SYSTEM_PROJECT",
    "BASE_SYSTEM_USER",
    "BASE_SYSTEM_PROJECT_USER",
    "T_ProjectContract_Out",
    "C_JFHKLR",
    "C_ZFSQGL",
    "T_FK_Supplier",
    "T_GYSHT_INFO",
    "C_ZFSQGL_CB",
    "C_JFHKLR_CB",
]

MANIFEST_SPECS = [
    ("project_sc_v1", "project", "manifest/project_external_id_manifest_v1.json", "project.project", ["legacy_key", "target_lookup.value"]),
    ("partner_sc_v1", "partner", "manifest/partner_external_id_manifest_v1.json", "res.partner", ["legacy_partner_id", "legacy_identity_key", "target_lookup.value"]),
    (
        "contract_counterparty_partner_sc_v1",
        "contract_counterparty_partner",
        "manifest/contract_counterparty_partner_external_id_manifest_v1.json",
        "res.partner",
        ["legacy_partner_id", "legacy_identity_key", "target_lookup.value"],
    ),
    (
        "receipt_counterparty_partner_sc_v1",
        "receipt_counterparty_partner",
        "manifest/receipt_counterparty_partner_external_id_manifest_v1.json",
        "res.partner",
        ["legacy_partner_id", "legacy_identity_key", "target_lookup.value"],
    ),
    ("user_sc_v1", "user", "manifest/user_external_id_manifest_v1.json", "res.users", ["legacy_user_id", "legacy_user_pid", "legacy_login"]),
    (
        "project_member_sc_v1",
        "project_member",
        "manifest/project_member_external_id_manifest_v1.json",
        "sc.project.member.staging",
        ["legacy_member_id", "legacy_project_id", "legacy_user_ref"],
    ),
    ("contract_sc_v1", "contract", "manifest/contract_external_id_manifest_v1.json", "construction.contract", ["legacy_contract_id", "legacy_project_id"]),
    (
        "contract_line_sc_v1",
        "contract_line",
        "manifest/contract_line_external_id_manifest_v1.json",
        "construction.contract.line",
        ["legacy_contract_id"],
    ),
    ("receipt_sc_v1", "receipt", "manifest/receipt_external_id_manifest_v1.json", "payment.request", ["legacy_receipt_id", "legacy_contract_id", "legacy_project_id", "legacy_partner_id"]),
    (
        "outflow_request_sc_v1",
        "outflow_request",
        "manifest/outflow_request_external_id_manifest_v1.json",
        "payment.request",
        ["legacy_outflow_id", "legacy_contract_id", "legacy_project_id", "legacy_partner_id"],
    ),
    (
        "actual_outflow_sc_v1",
        "actual_outflow",
        "manifest/actual_outflow_external_id_manifest_v1.json",
        "payment.request",
        ["legacy_actual_outflow_id", "legacy_request_id", "legacy_project_id", "legacy_partner_id"],
    ),
    (
        "supplier_contract_sc_v1",
        "supplier_contract",
        "manifest/supplier_contract_external_id_manifest_v1.json",
        "construction.contract",
        ["legacy_supplier_contract_id", "legacy_project_id", "legacy_partner_id"],
    ),
    (
        "supplier_contract_line_sc_v1",
        "supplier_contract_line",
        "manifest/supplier_contract_line_external_id_manifest_v1.json",
        "construction.contract.line",
        ["legacy_supplier_contract_id"],
    ),
    (
        "outflow_request_line_sc_v1",
        "outflow_request_line",
        "manifest/outflow_request_line_external_id_manifest_v1.json",
        "payment.request.line",
        ["legacy_outflow_line_id", "legacy_outflow_id"],
    ),
    (
        "receipt_invoice_line_sc_v1",
        "receipt_invoice_line",
        "manifest/receipt_invoice_line_external_id_manifest_v1.json",
        "sc.receipt.invoice.line",
        ["legacy_receipt_invoice_line_id", "legacy_receipt_id", "attachment_candidate_keys.Id", "attachment_candidate_keys.ZBID", "attachment_candidate_keys.FPID", "attachment_candidate_keys.FP_CB_Id", "attachment_candidate_keys.pid"],
    ),
]

PID_KEY_SOURCES = {
    "project": {"legacy_key": "BASE_SYSTEM_PROJECT", "target_lookup.value": "BASE_SYSTEM_PROJECT"},
    "user": {"legacy_user_id": "BASE_SYSTEM_USER", "legacy_user_pid": "BASE_SYSTEM_USER"},
    "project_member": {"legacy_member_id": "BASE_SYSTEM_PROJECT_USER"},
    "contract": {"legacy_contract_id": "T_ProjectContract_Out"},
    "contract_line": {"legacy_contract_id": "T_ProjectContract_Out"},
    "receipt": {"legacy_receipt_id": "C_JFHKLR"},
    "outflow_request": {"legacy_outflow_id": "C_ZFSQGL"},
    "actual_outflow": {"legacy_actual_outflow_id": "T_FK_Supplier"},
    "supplier_contract": {"legacy_supplier_contract_id": "T_GYSHT_INFO"},
    "supplier_contract_line": {"legacy_supplier_contract_id": "T_GYSHT_INFO"},
    "outflow_request_line": {"legacy_outflow_line_id": "C_ZFSQGL_CB"},
    "receipt_invoice_line": {"legacy_receipt_invoice_line_id": "C_JFHKLR_CB", "attachment_candidate_keys.Id": "C_JFHKLR_CB"},
}

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), ID) AS ID,
  CONVERT(nvarchar(max), PID) AS PID,
  CONVERT(nvarchar(max), BILLID) AS BILLID,
  CONVERT(nvarchar(max), BUSINESSID) AS BUSINESSID,
  CONVERT(nvarchar(max), ATTR_NAME) AS ATTR_NAME,
  CONVERT(nvarchar(max), FILESIZE) AS FILESIZE,
  CONVERT(nvarchar(max), DEL) AS DEL
FROM dbo.BASE_SYSTEM_FILE
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(ID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(PID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BILLID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(BUSINESSID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ATTR_NAME, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FILESIZE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY ID;
"""

SQL_COLUMNS = ["ID", "PID", "BILLID", "BUSINESSID", "ATTR_NAME", "FILESIZE", "DEL"]

SOURCE_PID_SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
SELECT CONCAT(source_table, @sep, source_id, @sep, source_pid) AS rowdata
FROM (
  SELECT 'BASE_SYSTEM_PROJECT' source_table, CONVERT(nvarchar(max), ID) source_id, CONVERT(nvarchar(max), PID) source_pid FROM dbo.BASE_SYSTEM_PROJECT
  UNION ALL SELECT 'BASE_SYSTEM_USER', CONVERT(nvarchar(max), ID), CONVERT(nvarchar(max), PID) FROM dbo.BASE_SYSTEM_USER
  UNION ALL SELECT 'BASE_SYSTEM_PROJECT_USER', CONVERT(nvarchar(max), ID), CONVERT(nvarchar(max), PID) FROM dbo.BASE_SYSTEM_PROJECT_USER
  UNION ALL SELECT 'T_ProjectContract_Out', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), PID) FROM dbo.T_ProjectContract_Out
  UNION ALL SELECT 'C_JFHKLR', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), PID) FROM dbo.C_JFHKLR
  UNION ALL SELECT 'C_ZFSQGL', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), PID) FROM dbo.C_ZFSQGL
  UNION ALL SELECT 'T_FK_Supplier', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), pid) FROM dbo.T_FK_Supplier
  UNION ALL SELECT 'T_GYSHT_INFO', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), PID) FROM dbo.T_GYSHT_INFO
  UNION ALL SELECT 'C_ZFSQGL_CB', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), pid) FROM dbo.C_ZFSQGL_CB
  UNION ALL SELECT 'C_JFHKLR_CB', CONVERT(nvarchar(max), Id), CONVERT(nvarchar(max), pid) FROM dbo.C_JFHKLR_CB
) src
WHERE NULLIF(LTRIM(RTRIM(source_id)), '') IS NOT NULL
  AND NULLIF(LTRIM(RTRIM(source_pid)), '') IS NOT NULL;
"""


class GlobalAttachmentScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GlobalAttachmentScreenError(message)


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


def run_source_pid_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -W -s '|'",
    ]
    completed = subprocess.run(cmd, input=SOURCE_PID_SQL, text=True, capture_output=True, check=False)
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
    require(len(rows) == EXPECTED_FILE_ROWS, f"file row count drifted: {len(rows)} != {EXPECTED_FILE_ROWS}")
    return rows


def is_deleted(value: object) -> bool:
    normalized = clean(value).lower()
    return bool(normalized) and normalized not in {"0", "false", "no", "n", "否"}


def load_source_pid_map() -> dict[tuple[str, str], str]:
    result: dict[tuple[str, str], str] = {}
    for line in run_source_pid_sql().splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != 3:
            continue
        table, source_id, source_pid = parts
        if table and source_id and source_pid:
            result[(table, source_id)] = source_pid
    require(result, "source pid map is empty")
    return result


def build_candidate_index(asset_root: Path) -> dict[str, list[dict[str, str]]]:
    source_pid = load_source_pid_map()
    index: dict[str, list[dict[str, str]]] = defaultdict(list)
    for package_id, lane, rel_path, target_model, key_paths in MANIFEST_SPECS:
        manifest = load_json(asset_root / rel_path)
        for row in manifest.get("records", []):
            if row.get("status") != "loadable":
                continue
            external_id = clean(row.get("external_id"))
            if not external_id:
                continue
            for key_path in key_paths:
                value = deep_get(row, key_path)
                if value:
                    index[value].append(
                        {
                            "package_id": package_id,
                            "lane": lane,
                            "target_model": target_model,
                            "external_id": external_id,
                            "candidate_key": key_path,
                        }
                    )
                    table = PID_KEY_SOURCES.get(lane, {}).get(key_path)
                    pid_value = source_pid.get((table, value)) if table else ""
                    if pid_value:
                        index[pid_value].append(
                            {
                                "package_id": package_id,
                                "lane": lane,
                                "target_model": target_model,
                                "external_id": external_id,
                                "candidate_key": f"{key_path}->source_pid",
                            }
                        )
    require(index, "global attachment candidate index is empty")
    return index


def screen(asset_root: Path) -> dict[str, Any]:
    index = build_candidate_index(asset_root)
    file_rows = parse_sql_rows(run_sql())
    per_lane: dict[str, Counter[str]] = defaultdict(Counter)
    per_lane_targets: dict[str, set[str]] = defaultdict(set)
    per_lane_files: dict[str, set[str]] = defaultdict(set)
    source_key_counts: Counter[str] = Counter()
    cross_lane_files: set[str] = set()
    ambiguous_same_lane_files: set[str] = set()
    deleted_matched_files = 0
    samples: list[dict[str, Any]] = []

    for row in file_rows:
        if is_deleted(row.get("DEL")):
            deleted = True
        else:
            deleted = False
        file_id = clean(row.get("ID"))
        matches: list[dict[str, str]] = []
        for source_field in SOURCE_FIELDS:
            source_value = clean(row.get(source_field))
            if not source_value:
                continue
            for candidate in index.get(source_value, []):
                match = dict(candidate)
                match["source_field"] = source_field
                match["source_value"] = source_value
                matches.append(match)
                source_key_counts[f"{source_field}->{candidate['candidate_key']}"] += 1
        if not matches:
            continue
        if deleted:
            deleted_matched_files += 1

        lanes = {match["lane"] for match in matches}
        if len(lanes) > 1:
            cross_lane_files.add(file_id)
        by_lane: dict[str, set[str]] = defaultdict(set)
        for match in matches:
            by_lane[match["lane"]].add(match["external_id"])
        if any(len(targets) > 1 for targets in by_lane.values()):
            ambiguous_same_lane_files.add(file_id)

        for lane, targets in by_lane.items():
            per_lane[lane]["matched_file_rows"] += 1
            per_lane[lane]["multi_target_file_rows"] += 1 if len(targets) > 1 else 0
            per_lane_files[lane].add(file_id)
            per_lane_targets[lane].update(targets)
        if len(samples) < 80:
            samples.append(
                {
                    "file_id": file_id,
                    "name": clean(row.get("ATTR_NAME")),
                    "deleted": deleted,
                    "lanes": sorted(lanes),
                    "match_count": len(matches),
                    "matches": matches[:8],
                }
            )

    lane_rows = []
    for package_id, lane, _rel_path, target_model, _key_paths in MANIFEST_SPECS:
        counters = per_lane[lane]
        matched_files = len(per_lane_files[lane])
        matched_targets = len(per_lane_targets[lane])
        if not matched_files:
            decision = "no_attachment_match"
        elif counters["multi_target_file_rows"]:
            decision = "blocked_same_lane_ambiguous"
        else:
            decision = "candidate_for_attachment_asset"
        lane_rows.append(
            {
                "package_id": package_id,
                "lane": lane,
                "target_model": target_model,
                "matched_file_rows": matched_files,
                "matched_target_records": matched_targets,
                "multi_target_file_rows": counters["multi_target_file_rows"],
                "decision": decision,
            }
        )

    return {
        "status": "PASS",
        "source_table": "BASE_SYSTEM_FILE",
        "file_rows": len(file_rows),
        "candidate_key_values": len(index),
        "lanes": lane_rows,
        "source_key_counts": dict(sorted(source_key_counts.items())),
        "cross_lane_file_rows": len(cross_lane_files),
        "ambiguous_same_lane_file_rows": len(ambiguous_same_lane_files),
        "deleted_matched_file_rows": deleted_matched_files,
        "samples": samples,
        "db_writes": 0,
        "odoo_shell": False,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lane_rows = "\n".join(
        "| {package_id} | {lane} | {target_model} | {matched_file_rows} | {matched_target_records} | {multi_target_file_rows} | {decision} |".format(
            **row
        )
        for row in payload["lanes"]
    )
    key_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["source_key_counts"].items()) or "| none | 0 |"
    next_lanes = [row for row in payload["lanes"] if row["decision"] == "candidate_for_attachment_asset" and row["lane"] != "receipt_invoice_line"]
    next_rows = "\n".join(
        f"| {row['lane']} | {row['target_model']} | {row['matched_file_rows']} | {row['matched_target_records']} |"
        for row in next_lanes
    ) or "| none |  | 0 | 0 |"
    return f"""# Legacy Global Attachment Screen v1

Status: `{payload["status"]}`

This read-only screen matches `BASE_SYSTEM_FILE` against all current business
external-id manifests. It does not generate attachments or copy file binaries.

## Result

- source table: `{payload["source_table"]}`
- file rows: `{payload["file_rows"]}`
- candidate key values: `{payload["candidate_key_values"]}`
- cross-lane matched file rows: `{payload["cross_lane_file_rows"]}`
- same-lane ambiguous file rows: `{payload["ambiguous_same_lane_file_rows"]}`
- deleted matched file rows: `{payload["deleted_matched_file_rows"]}`
- DB writes: `0`
- Odoo shell: `false`

## Lane Coverage

| Package | Lane | Target model | Matched files | Matched target records | Same-lane ambiguous files | Decision |
|---|---|---|---:|---:|---:|---|
{lane_rows}

## Source Match Distribution

| Source field -> candidate key | Matches |
|---|---:|
{key_rows}

## Next Attachment Asset Candidates

| Lane | Target model | Matched files | Matched target records |
|---|---|---:|---:|
{next_rows}

## Decision

Generate attachment URL assets next for `candidate_for_attachment_asset` lanes,
but avoid cross-lane blind merging. If one file matches multiple lanes, each
lane must be generated and verified as a separate package with explicit target
model and dependency.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen global legacy attachment linkage.")
    parser.add_argument("--asset-root", default=str(ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (GlobalAttachmentScreenError, json.JSONDecodeError, OSError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("GLOBAL_ATTACHMENT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "GLOBAL_ATTACHMENT_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "file_rows": payload["file_rows"],
                "candidate_key_values": payload["candidate_key_values"],
                "cross_lane_file_rows": payload["cross_lane_file_rows"],
                "ambiguous_same_lane_file_rows": payload["ambiguous_same_lane_file_rows"],
                "candidate_lanes": [
                    row["lane"] for row in payload["lanes"] if row["decision"] == "candidate_for_attachment_asset"
                ],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
