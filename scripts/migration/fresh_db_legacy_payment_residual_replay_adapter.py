#!/usr/bin/env python3
"""Build replay payload for legacy payment facts not covered by runtime requests."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_payment_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_payment_residual_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_pid",
    "payment_family",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "contract_legacy_id",
    "contract_no",
    "request_legacy_id",
    "planned_amount",
    "paid_amount",
    "invoice_amount",
    "payment_method",
    "bank_account",
    "handler_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "attachment_ref",
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


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'C_ZFSQGL' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.PID")} AS legacy_pid,
  'outflow_request' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), h.f_SQRQ, 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.f_XMID")} AS project_legacy_id,
  {clean_sql("h.f_XMMC")} AS project_name,
  {clean_sql("h.f_GYSID")} AS partner_legacy_id,
  {clean_sql("h.f_GYSMC")} AS partner_name,
  {clean_sql("h.f_GYSHTID")} AS contract_legacy_id,
  {clean_sql("h.f_GYSHTBH")} AS contract_no,
  '' AS request_legacy_id,
  {clean_sql("h.f_JHJE")} AS planned_amount,
  {clean_sql("h.f_SFJE")} AS paid_amount,
  '0' AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("h.FKZH")} AS bank_account,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.f_LRSJ, 121), '') AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("h.f_Remark")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_ZFSQGL h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
UNION ALL
SELECT
  'T_FK_Supplier' AS source_table,
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.pid")} AS legacy_pid,
  'actual_outflow' AS payment_family,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), h.f_FKRQ, 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(h.XMMC, h.f_LYXM, h.TSXMMC)")} AS project_name,
  {clean_sql("h.f_SupplierID")} AS partner_legacy_id,
  {clean_sql("h.f_SupplierName")} AS partner_name,
  {clean_sql("h.f_HTID")} AS contract_legacy_id,
  {clean_sql("h.f_HTHB")} AS contract_no,
  {clean_sql("h.f_ZFSQGLId")} AS request_legacy_id,
  {clean_sql("h.f_FKJE")} AS planned_amount,
  {clean_sql("h.f_FKJE")} AS paid_amount,
  {clean_sql("h.f_FPJE")} AS invoice_amount,
  {clean_sql("h.f_FKFSMC")} AS payment_method,
  {clean_sql("h.FKZH")} AS bank_account,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.f_LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.f_LRSJ, 121), '') AS created_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("COALESCE(h.f_BZ, h.Remark, h.BZ)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_FK_Supplier h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
ORDER BY source_table, legacy_record_id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
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


def scalar(sql: str) -> int:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return int(stripped)
    return 0


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_payment_residual_replay_adapter",
        "total_rows": rows,
        "outflow_request_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_ZFSQGL;"),
        "actual_outflow_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_FK_Supplier;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_payment_residual_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_PAYMENT_RESIDUAL_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
