#!/usr/bin/env python3
"""Build replay payload for legacy user-project scope facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_user_project_scope_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_user_project_scope_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_scope_key",
    "source_table",
    "legacy_assignment_id",
    "relation_name",
    "legacy_user_id",
    "company_legacy_id",
    "project_legacy_id",
    "scope_state",
    "created_by_legacy_user_id",
    "created_by_name",
    "created_time",
    "removed_by_legacy_user_id",
    "removed_by_name",
    "removed_time",
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


def write_rows(writer: csv.writer, sql: str) -> int:
    count = 0
    with subprocess.Popen(sqlcmd(sql), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
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


def current_scope_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'T_System_UserAndXXGL:' + {clean_sql("ID")} + ':' + CONVERT(varchar(20), ROW_NUMBER() OVER (PARTITION BY ID ORDER BY LRSJ, SSXMID, userid)) AS legacy_scope_key,
  'T_System_UserAndXXGL' AS source_table,
  {clean_sql("ID")} AS legacy_assignment_id,
  {clean_sql("SJBMC")} AS relation_name,
  {clean_sql("userid")} AS legacy_user_id,
  {clean_sql("SSGSID")} AS company_legacy_id,
  {clean_sql("SSXMID")} AS project_legacy_id,
  'current' AS scope_state,
  {clean_sql("LRRID")} AS created_by_legacy_user_id,
  {clean_sql("LRR")} AS created_by_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS created_time,
  '' AS removed_by_legacy_user_id,
  '' AS removed_by_name,
  '' AS removed_time,
  'source_table=T_System_UserAndXXGL' AS note,
  '1' AS active
FROM dbo.T_System_UserAndXXGL
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""


def history_scope_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'T_System_UserAndXXGL_History:' + {clean_sql("ID")} + ':' + CONVERT(varchar(20), ROW_NUMBER() OVER (PARTITION BY ID ORDER BY SCSJ, LRSJ, SSXMID, userid)) AS legacy_scope_key,
  'T_System_UserAndXXGL_History' AS source_table,
  {clean_sql("ID")} AS legacy_assignment_id,
  {clean_sql("SJBMC")} AS relation_name,
  {clean_sql("userid")} AS legacy_user_id,
  {clean_sql("SSGSID")} AS company_legacy_id,
  {clean_sql("SSXMID")} AS project_legacy_id,
  'removed' AS scope_state,
  {clean_sql("LRRID")} AS created_by_legacy_user_id,
  {clean_sql("LRR")} AS created_by_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS created_time,
  {clean_sql("SCRID")} AS removed_by_legacy_user_id,
  {clean_sql("SCR")} AS removed_by_name,
  COALESCE(CONVERT(varchar(23), SCSJ, 121), '') AS removed_time,
  'source_table=T_System_UserAndXXGL_History' AS note,
  '1' AS active
FROM dbo.T_System_UserAndXXGL_History
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        current_rows = write_rows(writer, current_scope_sql())
        history_rows = write_rows(writer, history_scope_sql())

    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_user_project_scope_replay_adapter",
        "current_rows": current_rows,
        "history_rows": history_rows,
        "total_rows": current_rows + history_rows,
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_user_project_scope_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_USER_PROJECT_SCOPE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
