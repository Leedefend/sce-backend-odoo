#!/usr/bin/env python3
"""Export old invoice cost progress report rows from MSSQL."""

from __future__ import annotations

import csv
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = Path(
    os.getenv(
        "LEGACY_INVOICE_COST_PROGRESS_REPORT_CSV",
        str(REPO_ROOT / "artifacts/migration/legacy_invoice_cost_progress_report_v1.csv"),
    )
)
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
MSSQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
MSSQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
MSSQL_DB = os.getenv("LEGACY_MSSQL_DB", "LegacyDb")

FIELDS = [
    "legacy_project_id",
    "legacy_project_name",
    "progress_receipt_amount",
    "output_invoice_amount",
    "input_invoice_amount",
    "cost_difference_amount",
    "import_batch",
]


def export_sql() -> str:
    return r"""
SET NOCOUNT ON;
DECLARE @XMID nvarchar(64)='fb0c4133-f011-44a4-a285-59cfd30aec27';
SELECT
  CONVERT(nvarchar(max), A.ID) AS legacy_project_id,
  CONVERT(nvarchar(max), A.XMMC) AS legacy_project_name,
  CONVERT(nvarchar(max), ISNULL(B.JZJE, 0)) AS progress_receipt_amount,
  CONVERT(nvarchar(max), ISNULL(C.KPZJE, 0)) AS output_invoice_amount,
  CONVERT(nvarchar(max), ISNULL(D.JXSBJE, 0)) AS input_invoice_amount,
  CONVERT(nvarchar(max), CASE
    WHEN ISNULL(ISNULL(C.KPZJE, 0) - ISNULL(D.JXSBJE, 0), 0) < 0 THEN 0
    ELSE ISNULL(C.KPZJE, 0) - ISNULL(D.JXSBJE, 0)
  END) AS cost_difference_amount,
  'legacy_invoice_cost_progress_report_v1' AS import_batch
FROM dbo.BASE_SYSTEM_PROJECT A
LEFT JOIN (
  SELECT SUM(f_JE) AS JZJE, XMID
  FROM dbo.C_JFHKLR
  WHERE ISNULL(del, 0)=0 AND DJZT=2 AND ISNULL(XMID, '')<>''
  GROUP BY XMID
) B ON A.ID=B.XMID
LEFT JOIN (
  SELECT SUM(B.JE) AS KPZJE, XMID
  FROM dbo.C_JXXP_XXKPDJ A
  INNER JOIN dbo.C_JXXP_XXKPDJ_CB B ON A.ID=B.ZBID
  WHERE ISNULL(del, 0)=0 AND DJZT=2 AND ISNULL(XMID, '')<>''
  GROUP BY XMID
) C ON A.ID=C.XMID
LEFT JOIN (
  SELECT SUM(D_SCBSJS_ZKPJE) AS JXSBJE, XMID
  FROM dbo.C_JXXP_ZYFPJJD
  WHERE ISNULL(del, 0)=0 AND DJZT=2 AND ISNULL(XMID, '')<>''
  GROUP BY XMID
) D ON A.ID=D.XMID
WHERE ISNULL(A.del, 0)=0
  AND (@XMID='fb0c4133-f011-44a4-a285-59cfd30aec27' OR A.ID=@XMID)
  AND (ISNULL(B.JZJE, 0)<>0 OR ISNULL(C.KPZJE, 0)<>0 OR ISNULL(D.JXSBJE, 0)<>0)
ORDER BY A.XMMC;
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
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stderr": completed.stderr[-2000:]})
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
