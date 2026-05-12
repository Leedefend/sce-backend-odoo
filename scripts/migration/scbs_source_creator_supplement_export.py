#!/usr/bin/env python3
"""Export SCBS source creator/time evidence for fact staging replay.

The base SCBS fact package is deliberately compact. This supplement preserves
old-system creator/time fields without relying on Odoo import metadata.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
INPUT_CSV = Path(os.getenv("SCBS_FACT_STAGING_CSV", ROOT / "artifacts/migration/scbs_fact_staging_v1.csv"))
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", ROOT / "artifacts/migration"))
OUTPUT_CSV = ARTIFACT_ROOT / "scbs_source_creator_supplement_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_source_creator_supplement_export_result_v1.json"
SQL_CONTAINER = os.getenv("SCBS_MSSQL_CONTAINER", os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-scbs"))
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("SCBS_MSSQL_DATABASE", os.getenv("LEGACY_MSSQL_DATABASE", "LegacyScbs20260417"))
CHUNK_SIZE = int(os.getenv("SCBS_SOURCE_CREATOR_CHUNK_SIZE", "500"))

SOURCE_COLUMNS = {
    "T_FK_Supplier": ("Id", "LRRID", "f_LRR", "f_LRSJ"),
    "T_GYSHT_INFO": ("Id", "LRRID", "f_LRR", "f_LRRQ"),
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


def read_required() -> dict[str, set[str]]:
    required: dict[str, set[str]] = {}
    with INPUT_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            table = clean(row.get("source_table"))
            legacy_id = clean(row.get("legacy_record_id"))
            if table in SOURCE_COLUMNS and legacy_id:
                required.setdefault(table, set()).add(legacy_id)
    return required


def chunks(values: list[str]):
    for index in range(0, len(values), CHUNK_SIZE):
        yield values[index : index + CHUNK_SIZE]


def parse_rows(output: str) -> list[dict[str, str]]:
    fields = ["source_table", "legacy_record_id", "creator_legacy_user_id", "creator_name", "created_time"]
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("("):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
        rows.append(dict(zip(fields, parts)))
    return rows


def query_chunk(table: str, record_ids: list[str]) -> list[dict[str, str]]:
    id_col, creator_id_col, creator_col, created_col = SOURCE_COLUMNS[table]
    values_sql = ", ".join(f"({sql_literal(item)})" for item in record_ids)
    sql = f"""
SET NOCOUNT ON;
WITH required(record_id) AS (
  SELECT * FROM (VALUES {values_sql}) v(record_id)
)
SELECT
  {sql_literal(table)} AS source_table,
  {clean_sql('src.' + id_col)} AS legacy_record_id,
  {clean_sql('src.' + creator_id_col)} AS creator_legacy_user_id,
  {clean_sql('src.' + creator_col)} AS creator_name,
  COALESCE(CONVERT(varchar(23), src.{created_col}, 121), '') AS created_time
FROM required r
JOIN dbo.{table} src ON CONVERT(varchar(max), src.{id_col}) = r.record_id
ORDER BY src.{id_col};
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
    return parse_rows(completed.stdout)


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["source_table", "legacy_record_id", "creator_legacy_user_id", "creator_name", "created_time"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    required = read_required()
    result_rows: list[dict[str, str]] = []
    for table, record_ids in sorted(required.items()):
        for part in chunks(sorted(record_ids)):
            result_rows.extend(query_chunk(table, part))
    write_csv(OUTPUT_CSV, result_rows)
    payload = {
        "status": "PASS",
        "mode": "scbs_source_creator_supplement_export",
        "input_csv": str(INPUT_CSV),
        "output_csv": str(OUTPUT_CSV),
        "required_counts": {table: len(ids) for table, ids in sorted(required.items())},
        "output_rows": len(result_rows),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_SOURCE_CREATOR_SUPPLEMENT_EXPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
