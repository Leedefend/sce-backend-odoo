#!/usr/bin/env python3
"""Build replay payload for legacy tender document purchase requests."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_tender_doc_purchase_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_tender_doc_purchase_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id",
    "legacy_pid",
    "source_table",
    "document_no",
    "document_state",
    "applicant_name",
    "apply_date",
    "project_legacy_id",
    "project_name",
    "tender_project_legacy_id",
    "tender_project_name",
    "receipt_partner_name",
    "receipt_bank_account",
    "receipt_bank_name",
    "amount",
    "note",
    "attachment_ref",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "receipt_payee_name",
    "payment_method",
    "active",
]


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), %s), ''), "
        "CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')" % field
    )


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker",
        "exec",
        SQL_CONTAINER,
        SQLCMD,
        "-b",
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-s",
        "\t",
        "-y",
        "0",
        "-Y",
        "0",
        "-Q",
        sql,
    ]


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("pid")} AS legacy_pid,
  'BGGL_ZTBJHT_TBBM_TBBMFSQ' AS source_table,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("SQR")} AS applicant_name,
  COALESCE(CONVERT(varchar(23), SQRQ, 121), '') AS apply_date,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("TBXMID")} AS tender_project_legacy_id,
  {clean_sql("TBXMMC")} AS tender_project_name,
  {clean_sql("SKDW")} AS receipt_partner_name,
  {clean_sql("SKZH")} AS receipt_bank_account,
  {clean_sql("KHH")} AS receipt_bank_name,
  {clean_sql("JE")} AS amount,
  {clean_sql("BZ")} AS note,
  {clean_sql("FJ")} AS attachment_ref,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS created_time,
  {clean_sql("SKR")} AS receipt_payee_name,
  {clean_sql("FKFS")} AS payment_method,
  CASE WHEN ISNULL(DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.BGGL_ZTBJHT_TBBM_TBBMFSQ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY LRSJ, Id;
"""


def write_csv_payload() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
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
    return count


def scalar(sql: str) -> str:
    raw = subprocess.check_output(sqlcmd(sql), text=True)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return stripped
    return "0"


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_tender_doc_purchase_adapter",
        "source_table": "BGGL_ZTBJHT_TBBM_TBBMFSQ",
        "total_rows": rows,
        "active_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_ZTBJHT_TBBM_TBBMFSQ WHERE ISNULL(DEL,0)=0;")),
        "amount_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(JE),0) FROM dbo.BGGL_ZTBJHT_TBBM_TBBMFSQ WHERE ISNULL(DEL,0)=0;"),
        "payload_csv": str(OUTPUT_CSV),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
