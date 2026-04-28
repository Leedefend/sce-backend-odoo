#!/usr/bin/env python3
"""Build replay payload for legacy expense reimbursement line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_expense_reimbursement_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_expense_reimbursement_line_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "document_no",
    "document_date",
    "document_state",
    "company_legacy_id",
    "company_name",
    "department_legacy_id",
    "department_name",
    "project_legacy_id",
    "project_name",
    "applicant_legacy_id",
    "applicant_name",
    "applicant_contact",
    "applicant_position",
    "reimbursement_type_legacy_id",
    "reimbursement_type",
    "finance_type_legacy_id",
    "finance_type",
    "line_project_legacy_id",
    "line_project_name",
    "line_date",
    "amount",
    "quantity",
    "unit_price",
    "allocated_amount",
    "summary",
    "participant",
    "participant_count",
    "deducted_participant",
    "deducted_count",
    "invoice_content",
    "payment_method",
    "payee",
    "payee_account",
    "payee_bank",
    "header_total",
    "requested_amount",
    "approved_amount",
    "writeoff_amount",
    "advance_amount",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "line_attachment_ref",
    "note",
    "header_note",
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
  {clean_sql("c.Id")} AS legacy_line_id,
  {clean_sql("c.ZBID")} AS legacy_header_id,
  {clean_sql("c.pid")} AS legacy_pid,
  {clean_sql("h.pid")} AS legacy_header_pid,
  {clean_sql("h.DJBH")} AS document_no,
  {clean_sql("h.RQ")} AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.SSGSID")} AS company_legacy_id,
  {clean_sql("h.SSGS")} AS company_name,
  {clean_sql("h.BMID")} AS department_legacy_id,
  {clean_sql("h.BM")} AS department_name,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.Personid")} AS applicant_legacy_id,
  {clean_sql("h.XM")} AS applicant_name,
  {clean_sql("h.LXFS")} AS applicant_contact,
  {clean_sql("h.ZW")} AS applicant_position,
  {clean_sql("c.BXLBID")} AS reimbursement_type_legacy_id,
  {clean_sql("c.BXLB")} AS reimbursement_type,
  {clean_sql("c.CWBXLBID")} AS finance_type_legacy_id,
  {clean_sql("c.CWBXLB")} AS finance_type,
  {clean_sql("c.XMID")} AS line_project_legacy_id,
  {clean_sql("c.XMMC")} AS line_project_name,
  {clean_sql("c.RQ")} AS line_date,
  {clean_sql("c.JE")} AS amount,
  {clean_sql("c.SL")} AS quantity,
  {clean_sql("c.DJ")} AS unit_price,
  {clean_sql("c.FTJE")} AS allocated_amount,
  {clean_sql("c.SXSM")} AS summary,
  {clean_sql("c.CYR")} AS participant,
  {clean_sql("c.WRS")} AS participant_count,
  {clean_sql("c.KCYR")} AS deducted_participant,
  {clean_sql("c.KRS")} AS deducted_count,
  {clean_sql("c.FPNR")} AS invoice_content,
  {clean_sql("h.FKFS")} AS payment_method,
  {clean_sql("h.SKR")} AS payee,
  {clean_sql("h.SKZH")} AS payee_account,
  {clean_sql("h.KHYH")} AS payee_bank,
  {clean_sql("h.HJ")} AS header_total,
  {clean_sql("h.SQBXJE")} AS requested_amount,
  {clean_sql("h.SJBXJE")} AS approved_amount,
  {clean_sql("h.HXJE")} AS writeoff_amount,
  {clean_sql("h.YJJE")} AS advance_amount,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("c.FJ")} AS line_attachment_ref,
  {clean_sql("c.BZ")} AS note,
  {clean_sql("h.BZ")} AS header_note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.CWGL_FYBX_CB c
LEFT JOIN dbo.CWGL_FYBX h ON h.Id = c.ZBID
WHERE NULLIF(LTRIM(RTRIM(c.Id)), '') IS NOT NULL
ORDER BY c.Id;
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
        "mode": "fresh_db_legacy_expense_reimbursement_line_replay_adapter",
        "total_rows": rows,
        "header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.CWGL_FYBX;")),
        "active_header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.CWGL_FYBX WHERE ISNULL(DEL,0)=0;")),
        "orphan_line_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.CWGL_FYBX_CB c LEFT JOIN dbo.CWGL_FYBX h ON h.Id=c.ZBID WHERE h.Id IS NULL;")),
        "line_amount": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(JE),0) FROM dbo.CWGL_FYBX_CB;"),
        "header_approved_amount": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(SJBXJE),0) FROM dbo.CWGL_FYBX;"),
        "min_document_date": scalar("SET NOCOUNT ON; SELECT MIN(RQ) FROM dbo.CWGL_FYBX;"),
        "max_document_date": scalar("SET NOCOUNT ON; SELECT MAX(RQ) FROM dbo.CWGL_FYBX;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_expense_reimbursement_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_EXPENSE_REIMBURSEMENT_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
