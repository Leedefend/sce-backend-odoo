#!/usr/bin/env python3
"""Extract missing source creator rows for partner business-fact gaps.

Input is the record-level gap CSV exported by business_fact_backfill_audit.py.
Output uses the same format consumed by partner_source_creator_backfill_write.py.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from collections import Counter
from pathlib import Path


ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
INPUT_CSV = Path(
    os.getenv(
        "PARTNER_SOURCE_CREATOR_SUPPLEMENT_REQUIRED_CSV",
        str(ROOT / "artifacts/business-fact-audit-local/sc_demo_record_gap/source_creator_supplement_required_records_v1.csv"),
    )
)
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(ROOT / "artifacts/migration/partner_source_creator_supplement_v1"),
    )
)
OUTPUT_CSV = ARTIFACT_ROOT / "partner_source_creator_supplement_from_legacy_mssql_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "partner_source_creator_supplement_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
CHUNK_SIZE = int(os.getenv("PARTNER_SOURCE_CREATOR_SUPPLEMENT_CHUNK_SIZE", "500"))

SOURCE_COLUMNS = {
    "T_FK_Supplier": {
        "id": "Id",
        "creator_id": "LRRID",
        "creator": "f_LRR",
        "created": "f_LRSJ",
    },
    "T_GYSHT_INFO": {
        "id": "Id",
        "creator_id": "LRRID",
        "creator": "f_LRR",
        "created": "f_LRRQ",
    },
}


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), "
        + field
        + "), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


def sql_literal(value: str) -> str:
    return "'" + clean(value).replace("'", "''") + "'"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-W",
        "-s",
        "\t",
        "-h",
        "-1",
        "-Q",
        sql,
    ]


def docker_container_state(container: str) -> str:
    completed = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Status}}", container],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return "missing"
    return clean(completed.stdout) or "unknown"


def fail_summary(reason: str, detail: object | None = None) -> None:
    summary = {
        "status": "BLOCKED",
        "mode": "partner_source_creator_supplement_adapter",
        "reason": reason,
        "detail": detail or {},
        "input_csv": str(INPUT_CSV),
        "output_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, summary)
    raise RuntimeError(summary)


def read_required(path: Path) -> dict[str, set[str]]:
    required: dict[str, set[str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            table = clean(row.get("legacy_source_table"))
            record_id = clean(row.get("legacy_record_id"))
            if table in SOURCE_COLUMNS and record_id:
                required.setdefault(table, set()).add(record_id)
    return required


def chunks(values: list[str], size: int):
    for index in range(0, len(values), size):
        yield values[index : index + size]


def query_chunk(table: str, record_ids: list[str]) -> list[dict[str, str]]:
    columns = SOURCE_COLUMNS[table]
    values_sql = ", ".join(f"({sql_literal(item)})" for item in record_ids)
    sql = f"""
SET NOCOUNT ON;
WITH required(record_id) AS (
  SELECT * FROM (VALUES {values_sql}) v(record_id)
)
SELECT
  {sql_literal(table)} AS source_table,
  {clean_sql('src.' + columns['id'])} AS legacy_record_id,
  {clean_sql('src.' + columns['creator_id'])} AS creator_legacy_user_id,
  {clean_sql('src.' + columns['creator'])} AS creator_name,
  COALESCE(CONVERT(varchar(23), src.{columns['created']}, 121), '') AS created_time
FROM required r
JOIN dbo.{table} src ON CONVERT(varchar(max), src.{columns['id']}) = r.record_id
WHERE NULLIF(LTRIM(RTRIM(COALESCE(CONVERT(varchar(max), src.{columns['creator']}), ''))), '') IS NOT NULL
ORDER BY src.{columns['id']};
"""
    completed = subprocess.run(sqlcmd(sql), text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "table": table,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    rows: list[dict[str, str]] = []
    fields = ["source_table", "legacy_record_id", "creator_legacy_user_id", "creator_name", "created_time"]
    for line in completed.stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("("):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
        rows.append(dict(zip(fields, parts)))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_table", "legacy_record_id", "creator_legacy_user_id", "creator_name", "created_time"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


container_state = docker_container_state(SQL_CONTAINER)
if container_state != "running":
    fail_summary("legacy_mssql_container_not_running", {"container": SQL_CONTAINER, "state": container_state})

required = read_required(INPUT_CSV)
result_rows: list[dict[str, str]] = []
try:
    for table, record_ids in sorted(required.items()):
        for part in chunks(sorted(record_ids), CHUNK_SIZE):
            result_rows.extend(query_chunk(table, part))
except Exception as exc:
    fail_summary("legacy_mssql_query_failed", {"error": str(exc)})

write_csv(OUTPUT_CSV, result_rows)
source_counts = Counter(row["source_table"] for row in result_rows)
summary = {
    "status": "PASS",
    "mode": "partner_source_creator_supplement_adapter",
    "input_csv": str(INPUT_CSV),
    "output_csv": str(OUTPUT_CSV),
    "required_counts": {table: len(record_ids) for table, record_ids in sorted(required.items())},
    "output_rows": len(result_rows),
    "output_source_counts": dict(sorted(source_counts.items())),
}
write_json(OUTPUT_JSON, summary)
print("PARTNER_SOURCE_CREATOR_SUPPLEMENT=" + json.dumps(summary, ensure_ascii=False, sort_keys=True))
