#!/usr/bin/env python3
"""Build replay payload for privacy-restricted legacy personnel movement facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_personnel_movement_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_personnel_movement_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_movement_id", "legacy_pid", "document_no", "person_legacy_id",
    "person_name", "movement_type", "movement_code", "department_legacy_id",
    "position_legacy_id", "entry_date", "leave_date", "leave_reason",
    "salary_month", "notify_user_legacy_ids", "notify_user_names",
    "creator_legacy_user_id", "creator_name", "created_time", "attachment_ref",
    "attachment_name", "attachment_path", "note", "active",
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


def movement_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_movement_id,
  {clean_sql("Pid")} AS legacy_pid,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("PersonId")} AS person_legacy_id,
  {clean_sql("PersonName")} AS person_name,
  {clean_sql("YDLX")} AS movement_type,
  {clean_sql("LX")} AS movement_code,
  {clean_sql("BMID")} AS department_legacy_id,
  {clean_sql("ZWID")} AS position_legacy_id,
  COALESCE(CONVERT(varchar(23), RZRQ, 121), '') AS entry_date,
  COALESCE(CONVERT(varchar(23), LZRQ, 121), '') AS leave_date,
  {clean_sql("LZYY")} AS leave_reason,
  {clean_sql("JZYF")} AS salary_month,
  {clean_sql("LZTZRYID")} AS notify_user_legacy_ids,
  {clean_sql("LZTZRY")} AS notify_user_names,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS created_time,
  {clean_sql("FJ")} AS attachment_ref,
  {clean_sql("f_FJRelName")} AS attachment_name,
  {clean_sql("f_FJPath")} AS attachment_path,
  {clean_sql("BZ")} AS note,
  '1' AS active
FROM dbo.PM_RYYDGL
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY Id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(movement_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
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


def text_scalar(sql: str) -> str:
    raw = run_sql(sql)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return stripped
    return ""


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_personnel_movement_replay_adapter",
        "total_rows": rows,
        "legacy_people": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT PersonId) FROM dbo.PM_RYYDGL;"),
        "legacy_departments": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT BMID) FROM dbo.PM_RYYDGL;"),
        "leave_date_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.PM_RYYDGL WHERE LZRQ IS NOT NULL;"),
        "min_entry_date": text_scalar("SET NOCOUNT ON; SELECT CONVERT(varchar(23), MIN(RZRQ), 121) FROM dbo.PM_RYYDGL;"),
        "max_entry_date": text_scalar("SET NOCOUNT ON; SELECT CONVERT(varchar(23), MAX(RZRQ), 121) FROM dbo.PM_RYYDGL;"),
        "payload_csv": str(OUTPUT_CSV),
        "privacy_boundary": "restricted_config_admin_only",
        "decision": "legacy_personnel_movement_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_PERSONNEL_MOVEMENT_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
