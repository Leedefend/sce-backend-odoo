#!/usr/bin/env python3
"""Build replay payload for legacy construction diary line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_construction_diary_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_construction_diary_line_replay_adapter_result_v1.json"

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
    "document_state",
    "title",
    "diary_type",
    "category",
    "project_legacy_id",
    "project_name",
    "construction_unit",
    "project_manager",
    "diary_date",
    "header_description",
    "header_note",
    "line_quality_legacy_id",
    "line_quality_name",
    "line_description",
    "business_legacy_id",
    "related_business_legacy_id",
    "related_quality_type",
    "handler_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "line_attachment_ref",
    "attachment_name",
    "attachment_path",
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
  {clean_sql("h.Pid")} AS legacy_header_pid,
  {clean_sql("h.DJBH")} AS document_no,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.BT")} AS title,
  {clean_sql("h.DJLX")} AS diary_type,
  {clean_sql("h.LB")} AS category,
  {clean_sql("h.f_XMID")} AS project_legacy_id,
  {clean_sql("h.f_GCMC")} AS project_name,
  {clean_sql("h.f_JSDW")} AS construction_unit,
  {clean_sql("h.f_XMJL")} AS project_manager,
  COALESCE(CONVERT(varchar(23), h.f_SJ, 121), '') AS diary_date,
  {clean_sql("h.f_SM")} AS header_description,
  {clean_sql("h.BZ")} AS header_note,
  {clean_sql("c.ZLID")} AS line_quality_legacy_id,
  {clean_sql("c.ZLMC")} AS line_quality_name,
  {clean_sql("c.ZLSM")} AS line_description,
  {clean_sql("h.GLYWID")} AS business_legacy_id,
  {clean_sql("c.D_SCBSJS_YWID")} AS related_business_legacy_id,
  {clean_sql("c.D_SCBSJS_ZLLX")} AS related_quality_type,
  {clean_sql("h.JBR")} AS handler_name,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("c.FJ")} AS line_attachment_ref,
  {clean_sql("c.f_FJRelName")} AS attachment_name,
  {clean_sql("c.f_FJPath")} AS attachment_path,
  CASE WHEN h.DEL IS NULL OR h.DEL = '0' THEN '1' ELSE '0' END AS active
FROM dbo.SGZL_RZRJ_CB c
LEFT JOIN dbo.SGZL_RZRJ h ON h.ID = c.ZBID
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
        "mode": "fresh_db_legacy_construction_diary_line_replay_adapter",
        "total_rows": rows,
        "header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.SGZL_RZRJ;")),
        "active_header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.SGZL_RZRJ WHERE DEL='0' OR DEL IS NULL;")),
        "orphan_line_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.SGZL_RZRJ_CB c LEFT JOIN dbo.SGZL_RZRJ h ON h.ID=c.ZBID WHERE h.ID IS NULL;")),
        "with_attachment_path_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.SGZL_RZRJ_CB WHERE NULLIF(LTRIM(RTRIM(CONVERT(varchar(max), f_FJPath))), '') IS NOT NULL;")),
        "min_diary_date": scalar("SET NOCOUNT ON; SELECT MIN(f_SJ) FROM dbo.SGZL_RZRJ;"),
        "max_diary_date": scalar("SET NOCOUNT ON; SELECT MAX(f_SJ) FROM dbo.SGZL_RZRJ;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_construction_diary_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_CONSTRUCTION_DIARY_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
