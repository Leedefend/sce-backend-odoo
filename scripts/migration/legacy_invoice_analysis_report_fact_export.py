#!/usr/bin/env python3
"""Export raw facts for the legacy invoice analysis report.

The old report SQLID 87d7d56f62494c99a0c339f303335813 combines construction
contract amount from T_ProjectContract_Out with input invoice amounts from
C_JXXP_ZYFPJJD, split by D_SCBSJS_FPGSLX.
"""

from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = Path(
    os.getenv(
        "LEGACY_INVOICE_ANALYSIS_REPORT_FACT_CSV",
        str(REPO_ROOT / "artifacts/migration/legacy_invoice_analysis_report_fact_v1.csv"),
    )
)
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
MSSQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
MSSQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
MSSQL_DB = os.getenv("LEGACY_MSSQL_DB", "LegacyDb")

FIELDS = [
    "legacy_source_table",
    "legacy_record_id",
    "fact_type",
    "legacy_project_id",
    "legacy_project_name",
    "invoice_company_type",
    "source_amount",
    "source_amount_field",
    "import_batch",
]


def export_sql() -> str:
    return r"""
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER OFF;
SELECT
  "T_ProjectContract_Out" AS legacy_source_table,
  CONVERT(nvarchar(max), ID) AS legacy_record_id,
  "contract_amount" AS fact_type,
  CONVERT(nvarchar(max), XMID) AS legacy_project_id,
  CONVERT(nvarchar(max), NULL) AS legacy_project_name,
  CONVERT(nvarchar(max), NULL) AS invoice_company_type,
  CONVERT(nvarchar(max), GCYSZJ) AS source_amount,
  "GCYSZJ" AS source_amount_field,
  "legacy_invoice_analysis_report_v1" AS import_batch
FROM dbo.T_ProjectContract_Out
WHERE ISNULL(DEL,0)=0 AND DJZT=2 AND ISNULL(XMID,"")<>""
UNION ALL
SELECT
  "C_JXXP_ZYFPJJD" AS legacy_source_table,
  CONVERT(nvarchar(max), ID) AS legacy_record_id,
  "input_invoice_amount" AS fact_type,
  CONVERT(nvarchar(max), XMID) AS legacy_project_id,
  CONVERT(nvarchar(max), XMMC) AS legacy_project_name,
  CONVERT(nvarchar(max), D_SCBSJS_FPGSLX) AS invoice_company_type,
  CONVERT(nvarchar(max), D_SCBSJS_ZKPJE) AS source_amount,
  "D_SCBSJS_ZKPJE" AS source_amount_field,
  "legacy_invoice_analysis_report_v1" AS import_batch
FROM dbo.C_JXXP_ZYFPJJD
WHERE ISNULL(DEL,0)=0 AND DJZT=2 AND ISNULL(XMID,"")<>""
ORDER BY legacy_source_table, legacy_record_id;
"""


def run_sql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        MSSQL_CONTAINER,
        SQLCMD,
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        MSSQL_PASSWORD,
        "-C",
        "-d",
        MSSQL_DB,
        "-s",
        "|",
        "-h",
        "-1",
    ]
    completed = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode:
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    return completed.stdout


def parse_rows(output: str) -> list[list[str]]:
    rows = []
    for line in output.splitlines():
        if not line.strip() or line.startswith("("):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "line": line[:500]})
        rows.append(parts)
    return rows


def main() -> None:
    rows = parse_rows(run_sql(export_sql()))
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        writer.writerows(rows)
    print({"path": str(OUTPUT_CSV), "rows": len(rows)})


if __name__ == "__main__":
    main()
