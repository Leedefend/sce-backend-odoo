#!/usr/bin/env python3
"""Build replay payload for legacy fund daily account line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_fund_daily_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_fund_daily_line_replay_adapter_result_v1.json"

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
    "title",
    "project_legacy_id",
    "project_name",
    "period_start",
    "period_end",
    "account_legacy_id",
    "account_name",
    "bank_account_no",
    "account_balance",
    "daily_income",
    "daily_expense",
    "current_account_balance",
    "current_bank_balance",
    "bank_system_difference",
    "header_account_balance_total",
    "header_bank_balance_total",
    "header_bank_system_difference",
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
  {clean_sql("c.ID")} AS legacy_line_id,
  {clean_sql("c.ZBID")} AS legacy_header_id,
  {clean_sql("c.PID")} AS legacy_pid,
  {clean_sql("h.PID")} AS legacy_header_pid,
  {clean_sql("h.DJBH")} AS document_no,
  COALESCE(CONVERT(varchar(10), COALESCE(c.RQ, h.DJRQ), 23), '') AS document_date,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.BT")} AS title,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  COALESCE(CONVERT(varchar(23), h.KSSJ, 121), '') AS period_start,
  COALESCE(CONVERT(varchar(23), h.JSSJ, 121), '') AS period_end,
  {clean_sql("c.ZHID")} AS account_legacy_id,
  {clean_sql("c.ZHMC")} AS account_name,
  {clean_sql("c.YHZH")} AS bank_account_no,
  {clean_sql("c.ZHWL")} AS account_balance,
  {clean_sql("c.DRLJSR")} AS daily_income,
  {clean_sql("c.DRLJZC")} AS daily_expense,
  {clean_sql("c.DQZHYE")} AS current_account_balance,
  {clean_sql("c.DQZHYHYE")} AS current_bank_balance,
  {clean_sql("c.YHXTCE")} AS bank_system_difference,
  {clean_sql("h.ZHYEHJ")} AS header_account_balance_total,
  {clean_sql("h.ZHYHYEHJ")} AS header_bank_balance_total,
  {clean_sql("h.YHXTCEHJ")} AS header_bank_system_difference,
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
FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB c
LEFT JOIN dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB h ON h.ID = c.ZBID
WHERE NULLIF(LTRIM(RTRIM(c.ID)), '') IS NOT NULL
ORDER BY COALESCE(h.DJRQ, c.RQ), c.ID;
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
        "mode": "fresh_db_legacy_fund_daily_line_replay_adapter",
        "total_rows": rows,
        "header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB;")),
        "active_header_rows": int(
            scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB WHERE ISNULL(DEL,0)=0;")
        ),
        "line_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB;")),
        "orphan_line_rows": int(
            scalar(
                """
                SET NOCOUNT ON;
                SELECT COUNT_BIG(*)
                FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB c
                LEFT JOIN dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB h ON h.ID = c.ZBID
                WHERE h.ID IS NULL;
                """
            )
        ),
        "daily_income_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(DRLJSR),0) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB;"),
        "daily_expense_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(DRLJZC),0) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB;"),
        "current_account_balance_sum": scalar(
            "SET NOCOUNT ON; SELECT COALESCE(SUM(DQZHYE),0) FROM dbo.D_SCBSJS_ZJGL_ZJSZ_ZJRBB_CB;"
        ),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_fund_daily_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_FUND_DAILY_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
