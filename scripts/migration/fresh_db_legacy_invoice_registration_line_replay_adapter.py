#!/usr/bin/env python3
"""Build replay payload for legacy invoice registration line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_invoice_registration_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_invoice_registration_line_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "project_legacy_id",
    "project_name",
    "fee_project_legacy_id",
    "fee_project_name",
    "document_no",
    "document_date",
    "invoice_date",
    "recognition_date",
    "invoice_no",
    "invoice_code",
    "invoice_type",
    "invoice_type_id",
    "supplier_legacy_id",
    "supplier_name",
    "supplier_tax_no",
    "amount_no_tax",
    "tax_amount",
    "amount_total",
    "tax_rate",
    "tax_rate_id",
    "quantity",
    "invoice_content",
    "cost_category_id",
    "cost_category_name",
    "contract_legacy_id",
    "settlement_legacy_id",
    "related_invoice_line_id",
    "related_invoice_line_no",
    "handler_name",
    "header_state",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modified_time",
    "invoice_holder",
    "accounting_state",
    "checksum",
    "voucher_no",
    "invoice_source",
    "project_cost_amount",
    "billing_unit",
    "attachment_ref",
    "attachment_name",
    "attachment_path",
    "note",
    "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


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


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def line_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("c.Id")} AS legacy_line_id,
  {clean_sql("c.ZBID")} AS legacy_header_id,
  {clean_sql("c.pid")} AS legacy_pid,
  {clean_sql("h.pid")} AS legacy_header_pid,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("c.FYXMID")} AS fee_project_legacy_id,
  {clean_sql("c.FYXM")} AS fee_project_name,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(23), h.DJRQ, 121), '') AS document_date,
  COALESCE(CONVERT(varchar(23), c.KPRQ, 121), '') AS invoice_date,
  COALESCE(CONVERT(varchar(23), c.RZRQ, 121), '') AS recognition_date,
  {clean_sql("c.FPHM")} AS invoice_no,
  {clean_sql("c.FPDM")} AS invoice_code,
  {clean_sql("c.FPLX")} AS invoice_type,
  {clean_sql("c.FPLXID")} AS invoice_type_id,
  {clean_sql("c.GYSID")} AS supplier_legacy_id,
  {clean_sql("c.GYSMC")} AS supplier_name,
  {clean_sql("c.GYSSH")} AS supplier_tax_no,
  {clean_sql("c.JE_NO")} AS amount_no_tax,
  {clean_sql("c.JXSE")} AS tax_amount,
  {clean_sql("c.HJJE")} AS amount_total,
  {clean_sql("c.SLV")} AS tax_rate,
  {clean_sql("c.SLV_ID")} AS tax_rate_id,
  {clean_sql("c.SL")} AS quantity,
  {clean_sql("c.FPNR")} AS invoice_content,
  {clean_sql("c.CBFLID")} AS cost_category_id,
  {clean_sql("c.CBFL")} AS cost_category_name,
  {clean_sql("COALESCE(NULLIF(c.GLHTID, ''), h.HTID)")} AS contract_legacy_id,
  {clean_sql("c.GLJSID")} AS settlement_legacy_id,
  {clean_sql("c.GLFPKPMXID")} AS related_invoice_line_id,
  {clean_sql("c.GLFPKPMXDH")} AS related_invoice_line_no,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.DJZT")} AS header_state,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("c.FPTGF")} AS invoice_holder,
  {clean_sql("c.SFHS")} AS accounting_state,
  {clean_sql("c.XYM")} AS checksum,
  {clean_sql("c.PZH")} AS voucher_no,
  {clean_sql("c.FPLY")} AS invoice_source,
  {clean_sql("c.DDSJJE")} AS project_cost_amount,
  {clean_sql("c.KPDW")} AS billing_unit,
  {clean_sql("COALESCE(NULLIF(c.FJ, ''), h.FJ)")} AS attachment_ref,
  {clean_sql("c.f_FJRelName")} AS attachment_name,
  {clean_sql("c.f_FJPath")} AS attachment_path,
  {clean_sql("COALESCE(NULLIF(c.BZ, ''), h.BZ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_JXXP_ZYFPJJD_CB c
LEFT JOIN dbo.C_JXXP_ZYFPJJD h ON h.Id = c.ZBID
WHERE NULLIF(LTRIM(RTRIM(c.Id)), '') IS NOT NULL
ORDER BY c.Id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(line_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
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
    return count


def scalar(sql: str) -> int:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return int(stripped)
    return 0


def decimal_scalar(sql: str) -> str:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return stripped
    return "0"


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_invoice_registration_line_replay_adapter",
        "total_rows": rows,
        "header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_JXXP_ZYFPJJD;"),
        "active_header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_JXXP_ZYFPJJD WHERE ISNULL(DEL,0)=0;"),
        "orphan_line_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_JXXP_ZYFPJJD_CB c LEFT JOIN dbo.C_JXXP_ZYFPJJD h ON h.Id=c.ZBID WHERE h.Id IS NULL;"),
        "amount_no_tax": decimal_scalar("SET NOCOUNT ON; SELECT SUM(COALESCE(JE_NO,0)) FROM dbo.C_JXXP_ZYFPJJD_CB;"),
        "tax_amount": decimal_scalar("SET NOCOUNT ON; SELECT SUM(COALESCE(JXSE,0)) FROM dbo.C_JXXP_ZYFPJJD_CB;"),
        "amount_total": decimal_scalar("SET NOCOUNT ON; SELECT SUM(COALESCE(HJJE,0)) FROM dbo.C_JXXP_ZYFPJJD_CB;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_invoice_registration_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_INVOICE_REGISTRATION_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
