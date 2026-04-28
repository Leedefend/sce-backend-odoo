#!/usr/bin/env python3
"""Build replay payloads for legacy account master records from LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
ACCOUNT_CSV = ARTIFACT_DIR / "fresh_db_legacy_account_master_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_account_master_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

ACCOUNT_FIELDS = [
    "legacy_account_id",
    "project_legacy_id",
    "project_name",
    "name",
    "account_no",
    "account_type",
    "opening_balance",
    "bank_name",
    "sort_no",
    "is_default",
    "fixed_account",
    "legacy_state",
    "source_table",
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


def write_sql_csv(path: Path, fields: list[str], sql: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with subprocess.Popen(sqlcmd(sql), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        if proc.stdout is None:
            raise RuntimeError("sqlcmd stdout unavailable")
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(fields)
            for line in proc.stdout:
                stripped = line.strip()
                if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
                    continue
                parts = line.rstrip("\r\n").split("\t")
                if len(parts) != len(fields):
                    raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
                writer.writerow(parts)
                count += 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code, "path": str(path)})
    return count


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("Id")} AS legacy_account_id,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(ZHMC)), ''), Id)")} AS name,
  {clean_sql("ZHHM")} AS account_no,
  {clean_sql("ZHLX")} AS account_type,
  {clean_sql("CQYE")} AS opening_balance,
  {clean_sql("KHH")} AS bank_name,
  {clean_sql("PXH")} AS sort_no,
  CASE WHEN ISNULL(IsDefault, 0) IN (1, '1') THEN '1' ELSE '0' END AS is_default,
  CASE WHEN ISNULL(SFGDZH, N'否') = N'是' THEN '1' ELSE '0' END AS fixed_account,
  {clean_sql("ZH_State")} AS legacy_state,
  'C_Base_ZHSZ' AS source_table,
  {clean_sql("'source_table=C_Base_ZHSZ; creator=' + COALESCE(LRR, '') + '; department=' + COALESCE(SJBMC, '')")} AS note,
  CASE WHEN ISNULL(DEL, '0') = '0' AND ISNULL(ZH_State, 1) = 1 THEN '1' ELSE '0' END AS active
FROM dbo.C_Base_ZHSZ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY ZHLX, ZHMC, Id;
"""
    rows = write_sql_csv(ACCOUNT_CSV, ACCOUNT_FIELDS, sql)
    payload = {
        "mode": "fresh_db_legacy_account_master_replay_adapter",
        "account_rows": rows,
        "csv": str(ACCOUNT_CSV),
        "source_table": "C_Base_ZHSZ",
        "decision": "legacy_account_master_payload_ready" if rows else "STOP_REVIEW_REQUIRED",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_ACCOUNT_MASTER_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
