#!/usr/bin/env python3
"""Extract legacy financing/borrowing audit fields for replay backfill."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_financing_loan_audit_facts_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_financing_loan_audit_facts_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_source_table",
    "legacy_record_id",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
]


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), "
        f"{field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


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


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'ZJGL_ZJSZ_DKGL_DKDJ' AS legacy_source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  {clean_sql("CONVERT(varchar(19), LRSJ, 120)")} AS created_time,
  {clean_sql("XGRID")} AS modifier_legacy_user_id,
  {clean_sql("XGR")} AS modifier_name,
  {clean_sql("CONVERT(varchar(19), XGSJ, 120)")} AS modified_time
FROM dbo.ZJGL_ZJSZ_DKGL_DKDJ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
UNION ALL
SELECT
  'ZJGL_ZCDFSZ_FXJK_JK' AS legacy_source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  {clean_sql("CONVERT(varchar(19), LRSJ, 120)")} AS created_time,
  {clean_sql("XGRID")} AS modifier_legacy_user_id,
  {clean_sql("XGR")} AS modifier_name,
  {clean_sql("CONVERT(varchar(19), XGSJ, 120)")} AS modified_time
FROM dbo.ZJGL_ZCDFSZ_FXJK_JK
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY legacy_source_table, legacy_record_id;
"""


def main() -> int:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with subprocess.Popen(sqlcmd(payload_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(FIELDS)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(FIELDS):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code})
    payload = {
        "status": "PASS",
        "mode": "fresh_db_financing_loan_audit_facts_adapter",
        "rows": count,
        "payload_csv": str(OUTPUT_CSV),
        "source_tables": ["ZJGL_ZJSZ_DKGL_DKDJ", "ZJGL_ZCDFSZ_FXJK_JK"],
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FINANCING_LOAN_AUDIT_FACTS_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
