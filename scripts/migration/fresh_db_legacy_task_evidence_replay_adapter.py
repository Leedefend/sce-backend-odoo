#!/usr/bin/env python3
"""Build replay payload for legacy task/todo evidence facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_task_evidence_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_task_evidence_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_task_id",
    "legacy_pid",
    "project_legacy_id",
    "project_name",
    "bill_no",
    "subject",
    "description",
    "start_time",
    "due_time",
    "finish_time",
    "done_flag",
    "executor_legacy_ids",
    "primary_executor_legacy_id",
    "participant_legacy_ids",
    "pc_url",
    "app_url",
    "source",
    "source_id",
    "source_icbd",
    "created_time",
    "modified_time",
    "creator_legacy_user_id",
    "modifier_legacy_user_id",
    "priority",
    "finish_remark",
    "finish_attachment_ref",
    "task_type",
    "creator_name",
    "modifier_name",
    "finish_name",
    "read_time",
    "read_state",
    "business_id",
    "business_name",
    "param_text",
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


def task_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("ID")} AS legacy_task_id,
  {clean_sql("PID")} AS legacy_pid,
  {clean_sql("PROJECTID")} AS project_legacy_id,
  {clean_sql("PROJECTNAME")} AS project_name,
  {clean_sql("BILLNO")} AS bill_no,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(SUBJECT)), ''), ID)")} AS subject,
  {clean_sql("DESCRIPTION")} AS description,
  COALESCE(CONVERT(varchar(23), STARTTIME, 121), '') AS start_time,
  COALESCE(CONVERT(varchar(23), DUETIME, 121), '') AS due_time,
  COALESCE(CONVERT(varchar(23), FINISHTIME, 121), '') AS finish_time,
  {clean_sql("DONE")} AS done_flag,
  {clean_sql("EXECUTORIDS")} AS executor_legacy_ids,
  CASE
    WHEN CHARINDEX(',', COALESCE(EXECUTORIDS, '')) > 0 THEN LEFT(EXECUTORIDS, CHARINDEX(',', EXECUTORIDS) - 1)
    WHEN CHARINDEX(';', COALESCE(EXECUTORIDS, '')) > 0 THEN LEFT(EXECUTORIDS, CHARINDEX(';', EXECUTORIDS) - 1)
    ELSE {clean_sql("EXECUTORIDS")}
  END AS primary_executor_legacy_id,
  {clean_sql("PARTICIPANTIDS")} AS participant_legacy_ids,
  {clean_sql("PCURL")} AS pc_url,
  {clean_sql("APPURL")} AS app_url,
  {clean_sql("SOURCE")} AS source,
  {clean_sql("SOURCEID")} AS source_id,
  {clean_sql("SOURCEICBD")} AS source_icbd,
  COALESCE(CONVERT(varchar(23), CREATEDTIME, 121), '') AS created_time,
  COALESCE(CONVERT(varchar(23), MODIFIEDTIME, 121), '') AS modified_time,
  {clean_sql("CREATORID")} AS creator_legacy_user_id,
  {clean_sql("MODIFIERID")} AS modifier_legacy_user_id,
  {clean_sql("PRIORITY")} AS priority,
  {clean_sql("FINISHREMARK")} AS finish_remark,
  {clean_sql("FINISHFJ")} AS finish_attachment_ref,
  {clean_sql("LX")} AS task_type,
  {clean_sql("CREATORNAME")} AS creator_name,
  {clean_sql("MODIFIEDNAME")} AS modifier_name,
  {clean_sql("FINISHNAME")} AS finish_name,
  COALESCE(CONVERT(varchar(23), READTIME, 121), '') AS read_time,
  {clean_sql("READSTATE")} AS read_state,
  {clean_sql("BUSINESSID")} AS business_id,
  {clean_sql("BUSINESSNAME")} AS business_name,
  {clean_sql("PARAM")} AS param_text,
  CASE WHEN ISNULL(DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.T_BASE_TASKDONE
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""


def write_csv_payload() -> int:
    count = 0
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with subprocess.Popen(sqlcmd(task_sql()), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
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
        "mode": "fresh_db_legacy_task_evidence_replay_adapter",
        "total_rows": rows,
        "active_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_BASE_TASKDONE WHERE ISNULL(DEL,0)=0;"),
        "done_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_BASE_TASKDONE WHERE ISNULL(DONE,0)=1;"),
        "read_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_BASE_TASKDONE WHERE ISNULL(READSTATE,0)=1;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_task_evidence_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_TASK_EVIDENCE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
