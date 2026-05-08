#!/usr/bin/env python3
"""Build replay payload for legacy tender registration facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_tender_registration_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_tender_registration_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_record_id",
    "legacy_pid",
    "source_dataset",
    "document_no",
    "document_state",
    "project_legacy_id",
    "project_name",
    "owner_name",
    "construction_unit_name",
    "project_manager_name",
    "contact_name",
    "registration_time",
    "bid_time",
    "opening_time",
    "guarantee_deadline",
    "created_time",
    "creator_name",
    "creator_legacy_user_id",
    "guarantee_amount",
    "document_fee_amount",
    "max_price",
    "tender_status",
    "bid_participation",
    "bid_method",
    "bid_opening_place",
    "bank_name",
    "bank_account",
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
        "-b",
        "-S",
        "localhost",
        "-U",
        "sa",
        "-P",
        SQL_PASSWORD,
        "-C",
        "-d",
        SQL_DATABASE,
        "-s",
        "\t",
        "-y",
        "0",
        "-Y",
        "0",
        "-Q",
        sql,
    ]


def run_sql(sql: str) -> str:
    return subprocess.check_output(sqlcmd(sql), text=True)


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("ID")} AS legacy_record_id,
  {clean_sql("PID")} AS legacy_pid,
  {clean_sql("SJBMC")} AS source_dataset,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("DJZT")} AS document_state,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("f_GCMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(YZMC, ''), NULLIF(D_ZTZH_ZBDW, ''), NULLIF(f_JSDW, ''))")} AS owner_name,
  {clean_sql("COALESCE(NULLIF(D_ZTZH_JSDW, ''), NULLIF(f_JSDW, ''))")} AS construction_unit_name,
  {clean_sql("COALESCE(NULLIF(XMJL, ''), NULLIF(XMJL1, ''), NULLIF(D_ZTZH_XMFJL, ''))")} AS project_manager_name,
  {clean_sql("COALESCE(NULLIF(f_LXR, ''), NULLIF(D_ZTZH_ZBDWLXR, ''), NULLIF(D_ZTZH_ZBDLJGLXR, ''))")} AS contact_name,
  COALESCE(CONVERT(varchar(23), f_BMSJ, 121), '') AS registration_time,
  COALESCE(CONVERT(varchar(23), f_TBSJ, 121), '') AS bid_time,
  COALESCE(CONVERT(varchar(23), KBSJ, 121), '') AS opening_time,
  COALESCE(CONVERT(varchar(23), BZJJZSJ, 121), '') AS guarantee_deadline,
  COALESCE(CONVERT(varchar(23), f_LRSJ, 121), '') AS created_time,
  {clean_sql("f_LRR")} AS creator_name,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("BZJJE")} AS guarantee_amount,
  {clean_sql("BMFJE")} AS document_fee_amount,
  {clean_sql("ZGXJ")} AS max_price,
  {clean_sql("TBZT")} AS tender_status,
  {clean_sql("COALESCE(NULLIF(SFTBText, ''), CONVERT(varchar(16), f_SFTB))")} AS bid_participation,
  {clean_sql("ZBFS")} AS bid_method,
  {clean_sql("COALESCE(NULLIF(KBDD, ''), NULLIF(D_ZTZH_KBDD, ''), NULLIF(BSDJDD, ''))")} AS bid_opening_place,
  {clean_sql("KHH")} AS bank_name,
  {clean_sql("KHZH")} AS bank_account,
  {clean_sql("FJ")} AS attachment_ref,
  {clean_sql("COALESCE(NULLIF(f_BZ, ''), NULLIF(D_ZTZH_ZBBZ, ''))")} AS note,
  CASE WHEN ISNULL(DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.P_ZTB_GCBMGL
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY f_LRSJ, ID;
"""


def write_csv_payload() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
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
        "mode": "fresh_db_legacy_tender_registration_replay_adapter",
        "total_rows": rows,
        "active_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.P_ZTB_GCBMGL WHERE ISNULL(DEL,0)=0;")),
        "project_count": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT XMID) FROM dbo.P_ZTB_GCBMGL WHERE NULLIF(LTRIM(RTRIM(XMID)), '') IS NOT NULL;")),
        "guarantee_amount_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(BZJJE),0) FROM dbo.P_ZTB_GCBMGL;"),
        "document_fee_amount_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(BMFJE),0) FROM dbo.P_ZTB_GCBMGL;"),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_tender_registration_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_TENDER_REGISTRATION_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
