#!/usr/bin/env python3
"""Build replay payload for legacy file index facts from LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_file_index_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_file_index_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_file_key",
    "source_table",
    "legacy_file_id",
    "legacy_pid",
    "bill_id",
    "bill_type",
    "business_id",
    "file_system_data_id",
    "file_name",
    "file_path",
    "preview_path",
    "file_md5",
    "file_size",
    "extension",
    "uploader_legacy_user_id",
    "uploader_name",
    "upload_time",
    "deleter_legacy_user_id",
    "deleter_name",
    "delete_time",
    "encrypted_flag",
    "temporary_flag",
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


def extension_for(file_name: str, file_path: str) -> str:
    candidate = (file_name or file_path or "").strip().split("?")[0].split("#")[0]
    leaf = candidate.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if "." not in leaf:
        return ""
    ext = leaf.rsplit(".", 1)[-1].lower().strip()
    return ext[:32]


def write_rows(writer: csv.writer, sql: str, source_field_count: int) -> int:
    count = 0
    with subprocess.Popen(sqlcmd(sql), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        for line in proc.stdout:
            stripped = line.strip()
            if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                continue
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) != source_field_count:
                raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": source_field_count, "line": line[:500]})
            parts.insert(13, extension_for(parts[8], parts[9]))
            writer.writerow(parts)
            count += 1
    return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code})
    return count


def base_system_file_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'BASE_SYSTEM_FILE:' + {clean_sql("ID")} AS legacy_file_key,
  'BASE_SYSTEM_FILE' AS source_table,
  {clean_sql("ID")} AS legacy_file_id,
  {clean_sql("PID")} AS legacy_pid,
  {clean_sql("BILLID")} AS bill_id,
  '' AS bill_type,
  {clean_sql("BUSINESSID")} AS business_id,
  '' AS file_system_data_id,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(ATTR_NAME)), ''), ID)")} AS file_name,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(ATTR_PATH)), ''), PREVIEW_PATH, ID)")} AS file_path,
  {clean_sql("PREVIEW_PATH")} AS preview_path,
  {clean_sql("FILEMD5")} AS file_md5,
  CONVERT(varchar(40), COALESCE(FILESIZE, 0)) AS file_size,
  {clean_sql("LRRID")} AS uploader_legacy_user_id,
  {clean_sql("LRR")} AS uploader_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS upload_time,
  {clean_sql("SCRID")} AS deleter_legacy_user_id,
  {clean_sql("SCR")} AS deleter_name,
  COALESCE(CONVERT(varchar(23), SCSJ, 121), '') AS delete_time,
  {clean_sql("COALESCE(CONVERT(varchar(20), ISENCRYPT), CONVERT(varchar(20), WJSFJM), '')")} AS encrypted_flag,
  {clean_sql("IsTemporary")} AS temporary_flag,
  {clean_sql("'source_table=BASE_SYSTEM_FILE; source=' + COALESCE(CONVERT(varchar(40), SOURCE), '') + '; group_company=' + COALESCE(GROUP_SSGSMC, '')")} AS note,
  CASE WHEN ISNULL(DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.BASE_SYSTEM_FILE
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""


def bill_file_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  'T_BILL_FILE:' + {clean_sql("KeyId")} AS legacy_file_key,
  'T_BILL_FILE' AS source_table,
  {clean_sql("KeyId")} AS legacy_file_id,
  {clean_sql("pid")} AS legacy_pid,
  {clean_sql("BillId")} AS bill_id,
  {clean_sql("BillType")} AS bill_type,
  '' AS business_id,
  {clean_sql("FileSystemDataId")} AS file_system_data_id,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(AttrName)), ''), KeyId)")} AS file_name,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(AttrPath)), ''), PreviewHtmlPath, KeyId)")} AS file_path,
  {clean_sql("PreviewHtmlPath")} AS preview_path,
  '' AS file_md5,
  CASE WHEN ISNUMERIC(SizeNum) = 1 THEN CONVERT(varchar(40), CAST(SizeNum AS bigint)) ELSE '0' END AS file_size,
  {clean_sql("LRRID")} AS uploader_legacy_user_id,
  {clean_sql("LRR")} AS uploader_name,
  COALESCE(CONVERT(varchar(23), LRSJ, 121), '') AS upload_time,
  {clean_sql("SCRID")} AS deleter_legacy_user_id,
  {clean_sql("SCR")} AS deleter_name,
  COALESCE(CONVERT(varchar(23), SCSJ, 121), '') AS delete_time,
  {clean_sql("COALESCE(CONVERT(varchar(20), IsEncrypt), CONVERT(varchar(20), WJSFJM), '')")} AS encrypted_flag,
  {clean_sql("IsTemporary")} AS temporary_flag,
  {clean_sql("'source_table=T_BILL_FILE; lx=' + COALESCE(LX, '') + '; pc_or_mobile=' + COALESCE(PcOrMobile, '')")} AS note,
  CASE WHEN ISNULL(IsDelete, '0') = '0' THEN '1' ELSE '0' END AS active
FROM dbo.T_BILL_FILE
WHERE NULLIF(LTRIM(RTRIM(KeyId)), '') IS NOT NULL
ORDER BY KeyId;
"""


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
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(FIELDS)
        base_rows = write_rows(writer, base_system_file_sql(), len(FIELDS) - 1)
        bill_rows = write_rows(writer, bill_file_sql(), len(FIELDS) - 1)

    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_file_index_replay_adapter",
        "base_system_file_rows": base_rows,
        "bill_file_rows": bill_rows,
        "total_rows": base_rows + bill_rows,
        "base_system_file_active_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BASE_SYSTEM_FILE WHERE ISNULL(DEL,0)=0;"),
        "bill_file_active_rows": scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.T_BILL_FILE WHERE ISNULL(IsDelete,'0')='0';"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_file_index_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_FILE_INDEX_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
