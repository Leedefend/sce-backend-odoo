#!/usr/bin/env python3
"""Export SCBS fund daily source amounts for enterprise document projection."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-scbs")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyScbs20260417")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration"))
OUTPUT_CSV = ARTIFACT_ROOT / "scbs_fund_daily_source_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_fund_daily_source_export_result_v1.json"

FIELDS = [
    "legacy_record_id",
    "legacy_pid",
    "document_no",
    "document_state",
    "document_date",
    "legacy_xmid",
    "legacy_xmmc",
    "subject",
    "note",
    "source_account_balance_total",
    "source_bank_balance_total",
    "source_bank_system_difference",
]


def clean_sql(field: str) -> str:
    return "REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), %s), CHAR(13), ' '), CHAR(10), ' '), '|', '/')" % field


def run_sqlcmd(sql: str) -> list[str]:
    cmd = [
        "docker",
        "exec",
        "-i",
        SQL_CONTAINER,
        "bash",
        "-lc",
        (
            f"{SQLCMD} -S localhost -U sa -P \"$MSSQL_SA_PASSWORD\" "
            f"-C -d {SQL_DATABASE} -h -1 -W -s '|' -i /dev/stdin"
        ),
    ]
    proc = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=True)
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("ID")} legacy_record_id,
  {clean_sql("ISNULL(PID, '')")} legacy_pid,
  {clean_sql("ISNULL(DJBH, '')")} document_no,
  {clean_sql("ISNULL(DJZT, '')")} document_state,
  ISNULL(CONVERT(varchar(10), DJRQ, 120), '') document_date,
  {clean_sql("ISNULL(XMID, '')")} legacy_xmid,
  {clean_sql("ISNULL(XMMC, '')")} legacy_xmmc,
  {clean_sql("ISNULL(BT, '')")} subject,
  {clean_sql("ISNULL(BZ, '')")} note,
  CAST(ISNULL(ZHYEHJ, 0) AS decimal(28,10)) source_account_balance_total,
  CAST(ISNULL(ZHYHYEHJ, 0) AS decimal(28,10)) source_bank_balance_total,
  CAST(ISNULL(YHXTCEHJ, 0) AS decimal(28,10)) source_bank_system_difference
FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB
WHERE ISNULL(DEL, 0) = 0
ORDER BY DJRQ, ID;
"""
    rows = []
    for line in run_sqlcmd(sql):
        parts = line.split("|")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_row": line, "expected_fields": FIELDS})
        rows.append(dict(zip(FIELDS, parts)))

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "status": "PASS",
        "database": SQL_DATABASE,
        "rows": len(rows),
        "account_balance_total": sum(float(row["source_account_balance_total"] or 0) for row in rows),
        "bank_balance_total": sum(float(row["source_bank_balance_total"] or 0) for row in rows),
        "bank_system_difference_total": sum(float(row["source_bank_system_difference"] or 0) for row in rows),
        "output_csv": str(OUTPUT_CSV),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_FUND_DAILY_SOURCE_EXPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
