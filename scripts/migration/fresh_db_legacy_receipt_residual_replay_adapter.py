#!/usr/bin/env python3
"""Build replay payload for legacy receipt facts not covered by runtime requests."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_receipt_residual_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_receipt_residual_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id",
    "legacy_pid",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "receipt_type",
    "income_category_legacy_id",
    "income_category",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "partner_type",
    "contract_legacy_id",
    "contract_no",
    "amount",
    "deducted_invoice_amount",
    "deducted_tax_amount",
    "settlement_amount",
    "budget_amount",
    "payment_method_legacy_id",
    "payment_method",
    "receiving_account_legacy_id",
    "receiving_account",
    "bill_no",
    "invoice_ref",
    "manager_legacy_id",
    "manager_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
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
  {clean_sql("h.Id")} AS legacy_record_id,
  {clean_sql("h.PID")} AS legacy_pid,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), h.f_RQ, 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.type")} AS receipt_type,
  {clean_sql("h.f_SRLBID")} AS income_category_legacy_id,
  {clean_sql("COALESCE(h.f_SRLBName, h.D_HLCSXT_SRLB)")} AS income_category,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.XMID)), ''), NULLIF(LTRIM(RTRIM(h.LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))")} AS project_legacy_id,
  {clean_sql("COALESCE(h.XMMC, h.LYXM, h.TSXMMC, h.JHMC)")} AS project_name,
  {clean_sql("h.WLDWID")} AS partner_legacy_id,
  {clean_sql("h.WLDWMC")} AS partner_name,
  {clean_sql("h.DWLX")} AS partner_type,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.SGHTID)), ''), NULLIF(LTRIM(RTRIM(h.GLHTID)), ''), NULLIF(LTRIM(RTRIM(h.HTID)), ''))")} AS contract_legacy_id,
  {clean_sql("COALESCE(h.SGHTBH, h.GLHTBH)")} AS contract_no,
  {clean_sql("h.f_JE")} AS amount,
  {clean_sql("h.f_KCFP")} AS deducted_invoice_amount,
  {clean_sql("h.f_KCSJ")} AS deducted_tax_amount,
  {clean_sql("h.CZJE")} AS settlement_amount,
  {clean_sql("h.YSJE")} AS budget_amount,
  {clean_sql("h.FKFSID")} AS payment_method_legacy_id,
  {clean_sql("h.FKFSMC")} AS payment_method,
  {clean_sql("h.SKZHID")} AS receiving_account_legacy_id,
  {clean_sql("h.SKZH")} AS receiving_account,
  {clean_sql("h.PJH")} AS bill_no,
  {clean_sql("h.FP")} AS invoice_ref,
  {clean_sql("h.XMJLID")} AS manager_legacy_id,
  {clean_sql("h.XMJLMC")} AS manager_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("COALESCE(h.LRR, h.f_LRR)")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), COALESCE(CONVERT(varchar(23), h.f_LRSJ, 121), '')) AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("h.f_BZ")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.C_JFHKLR h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
ORDER BY h.Id;
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
        "mode": "fresh_db_legacy_receipt_residual_replay_adapter",
        "total_rows": rows,
        "receipt_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_JFHKLR;"),
        "active_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.C_JFHKLR WHERE ISNULL(DEL,0)=0;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_receipt_residual_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_RECEIPT_RESIDUAL_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
