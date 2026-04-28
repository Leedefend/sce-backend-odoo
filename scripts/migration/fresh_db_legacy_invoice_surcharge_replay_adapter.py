#!/usr/bin/env python3
"""Build replay payload for legacy invoice surcharge facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_invoice_surcharge_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")

FIELDS = [
    "direction",
    "legacy_line_id",
    "legacy_header_id",
    "source_table",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "partner_credit_code",
    "invoice_no",
    "invoice_date",
    "surcharge_amount",
    "import_batch",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def text_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(REPLACE(ISNULL(CONVERT(varchar(max), "
        + field
        + "), ''), CHAR(31), ' '), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_sql(sql: str) -> str:
    cmd = [
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
        "-w",
        "65535",
        "-h",
        "-1",
        "-Q",
        sql,
    ]
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    sql = f"""
SET NOCOUNT ON;
SELECT
  'output' AS direction,
  {text_sql("c.Id")} AS legacy_line_id,
  {text_sql("c.ZBID")} AS legacy_header_id,
  'C_JXXP_XXKPDJ_CB' AS source_table,
  {text_sql("h.DJBH")} AS document_no,
  ISNULL(CONVERT(varchar(10), COALESCE(h.FPKJRQ, h.SQRQ), 23), '') AS document_date,
  {text_sql("h.DJZT")} AS document_state,
  CAST(ISNULL(h.DEL, 0) AS varchar(20)) AS deleted_flag,
  {text_sql("h.XMID")} AS project_legacy_id,
  {text_sql("h.XMMC")} AS project_name,
  {text_sql("h.D_JCLY_KPDWID")} AS partner_legacy_id,
  {text_sql("h.SPFMC")} AS partner_name,
  '' AS partner_credit_code,
  {text_sql("c.FPH")} AS invoice_no,
  ISNULL(CONVERT(varchar(10), c.KPRQ, 23), '') AS invoice_date,
  CAST(ISNULL(c.D_SCBSJS_FJS, 0) AS varchar(50)) AS surcharge_amount,
  'legacy_invoice_surcharge_v1' AS import_batch
FROM dbo.C_JXXP_XXKPDJ_CB c
JOIN dbo.C_JXXP_XXKPDJ h ON h.Id = c.ZBID
WHERE ISNULL(h.DJZT, '0') = '2'
  AND ISNULL(h.DEL, 0) = 0
UNION ALL
SELECT
  'input',
  {text_sql("c.Id")},
  {text_sql("c.ZBID")},
  'C_JXXP_ZYFPJJD_CB',
  {text_sql("h.DJBH")},
  ISNULL(CONVERT(varchar(10), h.DJRQ, 23), ''),
  {text_sql("h.DJZT")},
  CAST(ISNULL(h.DEL, 0) AS varchar(20)),
  {text_sql("h.XMID")},
  {text_sql("h.XMMC")},
  {text_sql("c.GYSID")},
  {text_sql("c.GYSMC")},
  {text_sql("c.GYSSH")},
  {text_sql("c.FPHM")},
  ISNULL(CONVERT(varchar(10), c.KPRQ, 23), ''),
  CAST(ISNULL(c.D_SCBSJS_FJS, 0) AS varchar(50)),
  'legacy_invoice_surcharge_v1'
FROM dbo.C_JXXP_ZYFPJJD_CB c
JOIN dbo.C_JXXP_ZYFPJJD h ON h.Id = c.ZBID
WHERE ISNULL(h.DJZT, '0') = '2'
  AND ISNULL(h.DEL, 0) = 0;
"""
    rows: list[dict[str, str]] = []
    for raw_line in run_sql(sql).splitlines():
        line = raw_line.rstrip("\r\n")
        if not line or line.startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
        rows.append(dict(zip(FIELDS, (clean(part) for part in parts))))

    write_csv(OUTPUT_CSV, rows)
    output_sum = sum(float(row["surcharge_amount"] or 0.0) for row in rows if row["direction"] == "output")
    input_sum = sum(float(row["surcharge_amount"] or 0.0) for row in rows if row["direction"] == "input")
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_invoice_surcharge_replay_adapter",
        "expected_rows": len(rows),
        "output_rows": sum(1 for row in rows if row["direction"] == "output"),
        "input_rows": sum(1 for row in rows if row["direction"] == "input"),
        "output_surcharge_amount": round(output_sum, 4),
        "input_surcharge_amount": round(input_sum, 4),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
