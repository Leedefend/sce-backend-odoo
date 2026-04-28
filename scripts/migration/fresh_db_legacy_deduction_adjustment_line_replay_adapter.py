#!/usr/bin/env python3
"""Build replay payload for legacy deduction/settlement adjustment line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_deduction_adjustment_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_deduction_adjustment_line_replay_adapter_result_v1.json"

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
    "document_no",
    "document_date",
    "document_state",
    "title",
    "fund_plan_legacy_id",
    "fund_plan_name",
    "fund_plan_no",
    "fund_confirmation_legacy_id",
    "deduction_account",
    "deduction_account_legacy_id",
    "adjustment_item_legacy_id",
    "adjustment_item_name",
    "accumulated_planned_amount",
    "accumulated_actual_amount",
    "current_planned_amount",
    "current_actual_amount",
    "returned_flag",
    "registrant_name",
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
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(23), h.DJRQ, 121), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.BTMC")} AS title,
  {clean_sql("h.ZJJHID")} AS fund_plan_legacy_id,
  {clean_sql("h.ZJJHMC")} AS fund_plan_name,
  {clean_sql("h.JHDH")} AS fund_plan_no,
  {clean_sql("h.ZJGL_SZQR_DKQRB_Id")} AS fund_confirmation_legacy_id,
  {clean_sql("h.KKZH")} AS deduction_account,
  {clean_sql("h.KKZHID")} AS deduction_account_legacy_id,
  {clean_sql("c.SJNRID")} AS adjustment_item_legacy_id,
  {clean_sql("c.SJNR")} AS adjustment_item_name,
  {clean_sql("c.LJYJS")} AS accumulated_planned_amount,
  {clean_sql("c.LJYYJS")} AS accumulated_actual_amount,
  {clean_sql("c.BCJHYJS")} AS current_planned_amount,
  {clean_sql("c.BCSJS")} AS current_actual_amount,
  {clean_sql("c.SFTH")} AS returned_flag,
  {clean_sql("h.DJR")} AS registrant_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("c.BZ")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_KK_SJDJB_CB c
LEFT JOIN dbo.T_KK_SJDJB h ON h.Id = c.ZBID
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
        "mode": "fresh_db_legacy_deduction_adjustment_line_replay_adapter",
        "total_rows": rows,
        "header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_KK_SJDJB;"),
        "active_header_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_KK_SJDJB WHERE ISNULL(DEL,0)=0;"),
        "orphan_line_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_KK_SJDJB_CB c LEFT JOIN dbo.T_KK_SJDJB h ON h.Id=c.ZBID WHERE h.Id IS NULL;"),
        "current_actual_amount": decimal_scalar("SET NOCOUNT ON; SELECT SUM(COALESCE(BCSJS,0)) FROM dbo.T_KK_SJDJB_CB;"),
        "current_planned_amount": decimal_scalar("SET NOCOUNT ON; SELECT SUM(COALESCE(BCJHYJS,0)) FROM dbo.T_KK_SJDJB_CB;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_deduction_adjustment_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_DEDUCTION_ADJUSTMENT_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
