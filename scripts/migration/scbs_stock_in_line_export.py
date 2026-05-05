#!/usr/bin/env python3
"""Export SCBS stock-in legacy lines for Odoo formal projection."""

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
OUTPUT_CSV = ARTIFACT_ROOT / "scbs_stock_in_legacy_lines_v1.csv"
OUTPUT_JSON = ARTIFACT_ROOT / "scbs_stock_in_line_export_result_v1.json"


FIELDS = [
    "legacy_record_id",
    "document_no",
    "document_date",
    "supplier_name",
    "legacy_gcmc",
    "legacy_line_id",
    "legacy_material_id",
    "material_name",
    "spec_model",
    "uom_text",
    "qty",
    "unit_price",
    "unit_price_no_tax",
    "amount",
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


def parse_decimal(value: str) -> str:
    if value in ("", "NULL"):
        return "0"
    return value


def main() -> None:
    ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("h.ID")} legacy_record_id,
  {clean_sql("ISNULL(h.RKDH, '')")} document_no,
  ISNULL(CONVERT(varchar(10), h.DJRQ, 120), '') document_date,
  {clean_sql("ISNULL(h.SupplierName, '')")} supplier_name,
  {clean_sql("ISNULL(h.GCMC, '')")} legacy_gcmc,
  {clean_sql("l.ID")} legacy_line_id,
  {clean_sql("ISNULL(l.CLID, '')")} legacy_material_id,
  {clean_sql("ISNULL(l.CLMC, '')")} material_name,
  {clean_sql("ISNULL(l.GGXH, '')")} spec_model,
  {clean_sql("ISNULL(l.DW, '')")} uom_text,
  CAST(ISNULL(l.SL, 0) AS decimal(28,10)) qty,
  CAST(ISNULL(l.DJ, 0) AS decimal(28,10)) unit_price,
  CAST(ISNULL(l.DJ_NO, 0) AS decimal(28,10)) unit_price_no_tax,
  CAST(ISNULL(l.HJ, 0) AS decimal(28,10)) amount
FROM dbo.T_RK_RKD h
JOIN dbo.T_RK_RKDCB l ON l.ZBID = h.ID
WHERE ISNULL(h.DEL, 0) = 0
ORDER BY h.ID, l.ID;
"""
    rows = []
    for line in run_sqlcmd(sql):
        parts = line.split("|")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_row": line, "expected_fields": FIELDS})
        row = dict(zip(FIELDS, parts))
        for key in ["qty", "unit_price", "unit_price_no_tax", "amount"]:
            row[key] = parse_decimal(row[key])
        rows.append(row)

    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    payload = {
        "status": "PASS",
        "database": SQL_DATABASE,
        "rows": len(rows),
        "headers": len({row["legacy_record_id"] for row in rows}),
        "amount": sum(float(row["amount"] or 0) for row in rows),
        "output_csv": str(OUTPUT_CSV),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("SCBS_STOCK_IN_LINE_EXPORT=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
