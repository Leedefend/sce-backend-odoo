#!/usr/bin/env python3
"""Build replay payload for privacy-restricted legacy attendance check-in facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_attendance_checkin_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_attendance_checkin_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_checkin_id", "legacy_pid", "legacy_user_id", "group_name",
    "checkin_type", "exception_type", "checkin_datetime", "checkin_date_text",
    "checkin_time_text", "department_legacy_id", "department_name",
    "project_legacy_id", "project_name", "location_title", "location_detail",
    "wifi_name", "wifi_mac", "latitude", "longitude", "media_refs", "notes",
    "created_time", "modified_time", "active",
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


def checkin_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_checkin_id,
  {clean_sql("pid")} AS legacy_pid,
  {clean_sql("userid")} AS legacy_user_id,
  {clean_sql("groupname")} AS group_name,
  {clean_sql("checkin_type")} AS checkin_type,
  {clean_sql("exception_type")} AS exception_type,
  COALESCE(CONVERT(varchar(23), checkin_DateTime, 121), '') AS checkin_datetime,
  {clean_sql("checkin_Date")} AS checkin_date_text,
  {clean_sql("checkin_TimeStr")} AS checkin_time_text,
  {clean_sql("deptid")} AS department_legacy_id,
  {clean_sql("deptname")} AS department_name,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("location_title")} AS location_title,
  {clean_sql("location_detail")} AS location_detail,
  {clean_sql("wifiname")} AS wifi_name,
  {clean_sql("wifimac")} AS wifi_mac,
  {clean_sql("lat")} AS latitude,
  {clean_sql("lng")} AS longitude,
  {clean_sql("mediaids")} AS media_refs,
  {clean_sql("notes")} AS notes,
  COALESCE(CONVERT(varchar(23), createdDate, 121), '') AS created_time,
  COALESCE(CONVERT(varchar(23), updatedDate, 121), '') AS modified_time,
  CASE WHEN ISNULL(del, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.CheckInData
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY Id;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(checkin_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
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
        "mode": "fresh_db_legacy_attendance_checkin_replay_adapter",
        "total_rows": rows,
        "active_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.CheckInData WHERE ISNULL(del,0)=0;"),
        "legacy_users": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT userid) FROM dbo.CheckInData;"),
        "project_refs": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT XMID) FROM dbo.CheckInData WHERE NULLIF(XMID,'') IS NOT NULL;"),
        "min_checkin_time": text_scalar("SET NOCOUNT ON; SELECT CONVERT(varchar(23), MIN(checkin_DateTime), 121) FROM dbo.CheckInData;"),
        "max_checkin_time": text_scalar("SET NOCOUNT ON; SELECT CONVERT(varchar(23), MAX(checkin_DateTime), 121) FROM dbo.CheckInData;"),
        "payload_csv": str(OUTPUT_CSV),
        "privacy_boundary": "restricted_config_admin_only",
        "decision": "legacy_attendance_checkin_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_ATTENDANCE_CHECKIN_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
