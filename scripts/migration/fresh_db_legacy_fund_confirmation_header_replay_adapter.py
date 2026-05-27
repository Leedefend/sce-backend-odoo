#!/usr/bin/env python3
"""Build replay payload for legacy fund confirmation header facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_fund_confirmation_header_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_fund_confirmation_header_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_header_id", "legacy_pid", "project_legacy_id", "project_name",
    "document_no", "period_no", "receipt_time", "contract_legacy_id",
    "contract_name", "contract_amount", "bid_date", "current_project_stage",
    "actual_fund_amount", "accumulated_invoice_amount", "filler_name",
    "document_state", "creator_legacy_user_id", "creator_name", "created_time",
    "modifier_legacy_user_id", "modifier_name", "modified_time",
    "related_receipt_ids", "application_balance_note", "invoice_receipt_note",
    "quality_return_note", "available_balance_note", "construction_deduction_note",
    "payable_construction_deduction_note", "attachment_ref", "note", "active",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def sqlcmd(sql: str) -> list[str]:
    return [
        "docker", "exec", SQL_CONTAINER, SQLCMD, "-S", "localhost", "-U", "sa",
        "-P", SQL_PASSWORD, "-C", "-d", SQL_DATABASE, "-W", "-s", "\t", "-h", "-1", "-Q", sql,
    ]


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def header_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("h.Id")} AS legacy_header_id,
  {clean_sql("h.pid")} AS legacy_pid,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.DJBH")} AS document_no,
  {clean_sql("h.QS")} AS period_no,
  COALESCE(CONVERT(varchar(23), h.SJ, 121), '') AS receipt_time,
  {clean_sql("h.SGDID")} AS contract_legacy_id,
  {clean_sql("h.SGD")} AS contract_name,
  {clean_sql("h.HTJE")} AS contract_amount,
  COALESCE(CONVERT(varchar(23), h.ZBRQ, 121), '') AS bid_date,
  {clean_sql("h.MQXXJD")} AS current_project_stage,
  {clean_sql("h.KPSKQK_BQS")} AS actual_fund_amount,
  {clean_sql("h.LJKPJE")} AS accumulated_invoice_amount,
  {clean_sql("h.TXR")} AS filler_name,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.C_JFHKLR_Ids")} AS related_receipt_ids,
  {clean_sql("h.SQLCYE_BZ")} AS application_balance_note,
  {clean_sql("h.KPSKQK_BZ")} AS invoice_receipt_note,
  {clean_sql("h.ZLKXTH_BZ")} AS quality_return_note,
  {clean_sql("h.BCKYZJYE_BZ")} AS available_balance_note,
  {clean_sql("h.SGDGCK_4")} AS construction_deduction_note,
  {clean_sql("h.YFSGDGCK_4")} AS payable_construction_deduction_note,
  {clean_sql("h.FJ")} AS attachment_ref,
  '' AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.ZJGL_SZQR_DKQRB h
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
ORDER BY h.Id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(header_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
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
                    raise RuntimeError({"unexpected_column_count": len(parts), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        rc = proc.wait()
    if rc:
        raise RuntimeError({"sqlcmd_failed": rc})
    return count


def scalar(sql: str) -> str:
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
        "mode": "fresh_db_legacy_fund_confirmation_header_replay_adapter",
        "total_rows": rows,
        "header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.ZJGL_SZQR_DKQRB;"),
        "active_header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.ZJGL_SZQR_DKQRB WHERE ISNULL(DEL,0)=0;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_fund_confirmation_header_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_FUND_CONFIRMATION_HEADER_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
