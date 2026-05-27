#!/usr/bin/env python3
"""Aggregate the legacy invoice analysis report using the old report SQL logic."""

from __future__ import annotations

import json
import os
import subprocess


SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
MSSQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
MSSQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
MSSQL_DB = os.getenv("LEGACY_MSSQL_DB", "LegacyDb")

FIELDS = [
    "rows",
    "contract_amount",
    "company_invoice_amount",
    "individual_invoice_amount",
    "company_ratio_sum",
    "individual_ratio_sum",
]


def old_report_sql() -> str:
    return r"""
SET NOCOUNT ON;
SET QUOTED_IDENTIFIER OFF;
WITH q AS (
  SELECT
    A.ID,
    A.XMMC,
    ISNULL(B.SGHTJE, 0) AS SGHTJE,
    ISNULL(C.GSFPJE, 0) AS GSFPJE,
    ISNULL(C.GTFPJE, 0) AS GTFPJE,
    CASE WHEN ISNULL(B.SGHTJE, 0) <= 0 THEN 0 ELSE ISNULL(C.GSFPJE, 0) / ISNULL(B.SGHTJE, 0) END AS GSHTBL,
    CASE WHEN ISNULL(B.SGHTJE, 0) <= 0 THEN 0 ELSE ISNULL(C.GTFPJE, 0) / ISNULL(B.SGHTJE, 0) END AS GTHTBL
  FROM dbo.BASE_SYSTEM_PROJECT A
  LEFT JOIN (
    SELECT SUM(GCYSZJ) AS SGHTJE, XMID
    FROM dbo.T_ProjectContract_Out
    WHERE ISNULL(DEL, 0) = 0 AND DJZT = 2 AND ISNULL(XMID, "") <> ""
    GROUP BY XMID
  ) B ON A.ID = B.XMID
  LEFT JOIN (
    SELECT
      SUM(CASE WHEN D_SCBSJS_FPGSLX = N'公司发票' THEN D_SCBSJS_ZKPJE ELSE 0 END) AS GSFPJE,
      SUM(CASE WHEN D_SCBSJS_FPGSLX = N'个体发票' THEN D_SCBSJS_ZKPJE ELSE 0 END) AS GTFPJE,
      XMID
    FROM dbo.C_JXXP_ZYFPJJD
    WHERE ISNULL(DEL, 0) = 0 AND DJZT = 2 AND ISNULL(XMID, "") <> ""
    GROUP BY XMID
  ) C ON A.ID = C.XMID
  WHERE ISNULL(A.DEL, 0) = 0
)
SELECT
  COUNT(*) AS rows,
  CONVERT(decimal(18, 2), SUM(SGHTJE)) AS contract_amount,
  CONVERT(decimal(18, 2), SUM(GSFPJE)) AS company_invoice_amount,
  CONVERT(decimal(18, 2), SUM(GTFPJE)) AS individual_invoice_amount,
  CONVERT(decimal(18, 6), SUM(GSHTBL)) AS company_ratio_sum,
  CONVERT(decimal(18, 6), SUM(GTHTBL)) AS individual_ratio_sum
FROM q
WHERE SGHTJE <> 0 OR GSFPJE <> 0 OR GTFPJE <> 0;
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


def main() -> None:
    rows = []
    for line in run_sql(old_report_sql()).splitlines():
        if not line.strip() or line.startswith("("):
            continue
        parts = [part.strip() for part in line.split("|")]
        if len(parts) == len(FIELDS):
            rows.append(dict(zip(FIELDS, parts)))
    if len(rows) != 1:
        raise RuntimeError({"unexpected_old_report_rows": rows})
    print(json.dumps(rows[0], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
