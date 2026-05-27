#!/usr/bin/env python3
"""Build replay payload for remaining legacy business facts across restored DBs."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
SCAN_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", str(ARTIFACT_DIR / "business_fact_upgrade")))
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_business_fact_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_business_fact_residual_replay_adapter_result_v1.json"

SOURCE_SPEC = os.getenv(
    "LEGACY_BUSINESS_FACT_SOURCES",
    "main:legacy-mssql-restore:LegacyDb,scbs:legacy-mssql-scbs:LegacyScbs20260417",
)
SOURCE_TABLE_ALLOWLIST = {
    item.strip()
    for item in os.getenv("LEGACY_BUSINESS_FACT_TABLES", "").split(",")
    if item.strip()
}
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

FIELDS = [
    "source_label",
    "source_container",
    "source_database",
    "source_table",
    "source_dataset",
    "legacy_record_id",
    "legacy_parent_id",
    "legacy_pid",
    "family",
    "classification",
    "business_signal_score",
    "document_no",
    "document_date",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "amount_total",
    "raw_payload",
    "active",
]

ID_CANDIDATES = ("Id", "ID", "id", "Guid", "GUID", "BillID", "BILLID", "Pid", "PID")
PARENT_CANDIDATES = ("ZBID", "ParentID", "PARENTID", "PID", "Pid", "business_Id", "f_ZFSQGLId")
PID_CANDIDATES = ("pid", "Pid", "PID")
DATASET_CANDIDATES = ("SJBMC", "TableName")
DOC_CANDIDATES = ("DJBH", "DJH", "RKDH", "CKDH", "HTBH", "BH", "DJNO", "BillNo", "LYBH", "f_ZRDH")
DATE_CANDIDATES = ("DJRQ", "RQ", "LRSJ", "LRRQ", "GXSJ", "CreateTime", "CREATETIME", "f_LRSJ", "KSRQ")
PROJECT_ID_CANDIDATES = ("XMID", "f_XMID", "PROJECT_ID", "ProjectID", "LYXMID")
PROJECT_NAME_CANDIDATES = ("XMMC", "ProjectName", "f_GCMC", "GCMC", "DRXMMC", "GLXMMC")
PARTNER_ID_CANDIDATES = ("Supplier_ID", "GYSID", "f_GYSID", "f_Supplier_ID", "DWID", "WLDWID", "FBDWID", "SKDWID")
PARTNER_NAME_CANDIDATES = ("SupplierName", "GYSMC", "f_SupplierName", "DWMC", "WLDW", "FBDW", "SKDW", "LWGS")
AMOUNT_CANDIDATES = ("JE", "ZJE", "HJ", "RK_ZJE", "FYXJE", "HTJE", "f_HTJE", "JSHJ", "SE", "BZJJE")
DELETE_KEYS = ("DEL", "SCRQ", "SCRID", "IsDelete", "DELETED")
BUSINESS_CLASSES = {
    "candidate_effective_business_fact",
    "candidate_secondary_business_fact",
    "candidate_needs_manual_screen",
}


def parse_sources(raw: str) -> list[dict[str, str]]:
    sources = []
    for item in raw.split(","):
        parts = [part.strip() for part in item.split(":")]
        if len(parts) != 3 or not all(parts):
            raise RuntimeError({"invalid_legacy_business_fact_source": item, "expected": "label:container:database"})
        label, container, database = parts
        sources.append({"label": label, "container": container, "database": database})
    return sources


def source_scan_root(label: str) -> Path:
    return SCAN_ROOT if label == "main" else SCAN_ROOT / label


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def sql_identifier(name: str) -> str:
    return "[" + name.replace("]", "]]") + "]"


def run_sql(source: dict[str, str], sql: str) -> str:
    command = [
        "docker",
        "exec",
        "-i",
        source["container"],
        "bash",
        "-lc",
        f"{SQLCMD} -S localhost -U sa -P {shell_quote(SQL_PASSWORD)} -C -d {shell_quote(source['database'])} -s '\t' -y 0 -Y 0",
    ]
    completed = subprocess.run(command, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "source": source,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    return completed.stdout


def table_columns(source: dict[str, str], table: str) -> list[str]:
    sql = f"""
SET NOCOUNT ON;
SELECT c.name
FROM sys.columns c
JOIN sys.tables t ON t.object_id = c.object_id
JOIN sys.schemas s ON s.schema_id = t.schema_id
WHERE s.name = 'dbo' AND t.name = N'{table.replace("'", "''")}'
ORDER BY c.column_id;
"""
    columns = []
    for line in run_sql(source, sql).splitlines():
        value = line.strip()
        if not value or value == "name" or set(value) <= {"-"} or value.startswith("("):
            continue
        columns.append(value)
    return columns


def choose(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    column_set = set(columns)
    for candidate in candidates:
        if candidate in column_set:
            return candidate
    lower = {column.lower(): column for column in columns}
    for candidate in candidates:
        if candidate.lower() in lower:
            return lower[candidate.lower()]
    return None


def load_candidate_tables(label: str) -> list[dict[str, Any]]:
    path = source_scan_root(label) / "legacy_db_full_business_fact_loss_scan_v1.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    seen = set()
    for table in payload.get("tables") or []:
        name = table["table"]
        if SOURCE_TABLE_ALLOWLIST and name not in SOURCE_TABLE_ALLOWLIST:
            continue
        if name in seen or table.get("classification") not in BUSINESS_CLASSES or int(table.get("row_count") or 0) <= 0:
            continue
        seen.add(name)
        rows.append(
            {
                "family": table.get("family") or "",
                "table": name,
                "classification": table.get("classification") or "candidate_business_fact",
                "score": int(table.get("business_signal_score") or 0),
                "rows": int(table.get("row_count") or 0),
            }
        )
    rows.sort(key=lambda row: (str(row["family"]), -int(row["score"]), -int(row["rows"]), str(row["table"])))
    if SOURCE_TABLE_ALLOWLIST:
        for name in sorted(SOURCE_TABLE_ALLOWLIST - seen):
            rows.append(
                {
                    "family": "manual_allowlist",
                    "table": name,
                    "classification": "manual_allowlist",
                    "score": 0,
                    "rows": 0,
                }
            )
    return rows


def normalize_decimal(value: Any) -> str:
    if value in (None, ""):
        return ""
    try:
        return str(Decimal(str(value).replace(",", "")))
    except (InvalidOperation, ValueError):
        return ""


def first_payload_value(payload: dict[str, Any], candidates: tuple[str, ...]) -> str:
    for candidate in candidates:
        if candidate in payload and payload[candidate] not in (None, ""):
            return str(payload[candidate])
    lower = {key.lower(): key for key in payload}
    for candidate in candidates:
        key = lower.get(candidate.lower())
        if key and payload.get(key) not in (None, ""):
            return str(payload[key])
    return ""


def active_from_payload(payload: dict[str, Any], columns: list[str]) -> str:
    column_set = set(columns)
    if "DEL" in column_set:
        value = first_payload_value(payload, ("DEL",))
        return "1" if value.strip().lower() in {"", "0", "false", "none"} else "0"
    if "SCRQ" in column_set:
        value = first_payload_value(payload, ("SCRQ",))
        return "0" if value.strip() else "1"
    return "1"


def row_sql(table: str, id_column: str | None) -> str:
    if id_column:
        id_expr = (
            "CONCAT("
            f"COALESCE(NULLIF(CONVERT(varchar(200), src.{sql_identifier(id_column)}), ''), '__row__'),"
            "'#', src.__legacy_rownum)"
        )
    else:
        id_expr = "CONCAT('__row__', src.__legacy_rownum)"
    return f"""
SET NOCOUNT ON;
SELECT
  {id_expr} AS legacy_record_id,
  (SELECT src.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS raw_payload
FROM (
  SELECT *, ROW_NUMBER() OVER (ORDER BY (SELECT 1)) AS __legacy_rownum
  FROM dbo.{sql_identifier(table)}
) src
ORDER BY src.__legacy_rownum;
"""


def build_rows() -> tuple[list[dict[str, str]], dict[str, Any]]:
    output_rows: list[dict[str, str]] = []
    source_summaries = []
    source_table_counts: dict[str, int] = {}
    for source in parse_sources(SOURCE_SPEC):
        tables = load_candidate_tables(source["label"])
        source_row_count = 0
        for table_meta in tables:
            table = table_meta["table"]
            columns = table_columns(source, table)
            id_column = choose(columns, ID_CANDIDATES)
            for raw in run_sql(source, row_sql(table, id_column)).splitlines():
                if not raw.strip() or raw.startswith("legacy_record_id") or set(raw.strip()) <= {"-", "\t"} or raw.startswith("("):
                    continue
                parts = raw.split("\t", 1)
                if len(parts) != 2:
                    continue
                legacy_record_id, raw_payload = parts
                if not raw_payload.strip():
                    continue
                try:
                    payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    payload = {"_raw": raw_payload}
                row = {
                    "source_label": source["label"],
                    "source_container": source["container"],
                    "source_database": source["database"],
                    "source_table": table,
                    "source_dataset": first_payload_value(payload, DATASET_CANDIDATES),
                    "legacy_record_id": legacy_record_id,
                    "legacy_parent_id": first_payload_value(payload, PARENT_CANDIDATES),
                    "legacy_pid": first_payload_value(payload, PID_CANDIDATES),
                    "family": str(table_meta["family"]),
                    "classification": str(table_meta["classification"]),
                    "business_signal_score": str(table_meta["score"]),
                    "document_no": first_payload_value(payload, DOC_CANDIDATES),
                    "document_date": first_payload_value(payload, DATE_CANDIDATES),
                    "project_legacy_id": first_payload_value(payload, PROJECT_ID_CANDIDATES),
                    "project_name": first_payload_value(payload, PROJECT_NAME_CANDIDATES),
                    "partner_legacy_id": first_payload_value(payload, PARTNER_ID_CANDIDATES),
                    "partner_name": first_payload_value(payload, PARTNER_NAME_CANDIDATES),
                    "amount_total": normalize_decimal(first_payload_value(payload, AMOUNT_CANDIDATES)),
                    "raw_payload": json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    "active": active_from_payload(payload, columns),
                }
                output_rows.append(row)
                source_row_count += 1
                key = f"{source['database']}:{table}"
                source_table_counts[key] = source_table_counts.get(key, 0) + 1
        source_summaries.append({"source": source, "tables": len(tables), "rows": source_row_count})
    summary = {
        "sources": source_summaries,
        "total_rows": len(output_rows),
        "active_rows": sum(1 for row in output_rows if row["active"] == "1"),
        "table_count": len({(row["source_database"], row["source_table"]) for row in output_rows}),
        "source_table_counts": dict(sorted(source_table_counts.items())),
        "family_counts": {},
    }
    for row in output_rows:
        summary["family_counts"][row["family"]] = summary["family_counts"].get(row["family"], 0) + 1
    return output_rows, summary


def main() -> int:
    rows, summary = build_rows()
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_business_fact_residual_replay_adapter",
        "scan_root": str(SCAN_ROOT),
        "payload_csv": str(OUTPUT_CSV.relative_to(REPO_ROOT)),
        **summary,
        "decision": "full_candidate_legacy_business_fact_residual_payload_ready",
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FRESH_DB_LEGACY_BUSINESS_FACT_RESIDUAL_REPLAY_ADAPTER="
        + json.dumps(
            {
                "status": payload["status"],
                "total_rows": payload["total_rows"],
                "active_rows": payload["active_rows"],
                "table_count": payload["table_count"],
                "payload_csv": payload["payload_csv"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
