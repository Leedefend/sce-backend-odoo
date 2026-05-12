#!/usr/bin/env python3
"""Build replay payload for legacy social-security registration facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_social_security_registration_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_social_security_registration_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_line_id",
    "legacy_header_id",
    "document_no",
    "document_state",
    "period_year",
    "period_month",
    "project_legacy_id",
    "project_name",
    "employee_legacy_id",
    "employee_name",
    "department_name",
    "position_name",
    "payer_unit",
    "person_type",
    "amount",
    "contact",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
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


def payload_sql() -> str:
    return f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("c.Id")} AS legacy_line_id,
  {clean_sql("c.ZBID")} AS legacy_header_id,
  {clean_sql("COALESCE(h.DJBH, c.DJBH)")} AS document_no,
  {clean_sql("COALESCE(h.DJZT, c.DJZT)")} AS document_state,
  {clean_sql("COALESCE(h.ND, c.ND)")} AS period_year,
  {clean_sql("COALESCE(h.YF, c.YF)")} AS period_month,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("COALESCE(h.XMMC, c.XMMC)")} AS project_name,
  {clean_sql("c.RYID")} AS employee_legacy_id,
  {clean_sql("c.RY")} AS employee_name,
  {clean_sql("c.BM")} AS department_name,
  {clean_sql("c.GW")} AS position_name,
  {clean_sql("COALESCE(c.SSGS, c.KHCJ, h.XMMC)")} AS payer_unit,
  {clean_sql("c.D_SCBSJS_RYLX")} AS person_type,
  {clean_sql("c.JXGZ")} AS amount,
  {clean_sql("c.D_SCBSJS_LXFS")} AS contact,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("COALESCE(h.BZ, c.JL)")} AS note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 AND ISNULL(h.DJZT, '0') = '2' THEN '1' ELSE '0' END AS active
FROM dbo.BGGL_XZ_JXDJ c
LEFT JOIN dbo.BGGL_XZ_JXDJ_ZB h ON h.Id = c.ZBID
WHERE NULLIF(LTRIM(RTRIM(c.Id)), '') IS NOT NULL
  AND ISNULL(c.JXGZ, 0) <> 0
ORDER BY COALESCE(h.ND, c.ND), COALESCE(h.YF, c.YF), c.Id;
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
    raw = subprocess.check_output(sqlcmd(sql), text=True)
    for line in raw.splitlines():
        stripped = line.strip()
        if stripped and not (stripped.startswith("(") and stripped.endswith("rows affected)")):
            return stripped
    return "0"


def main() -> int:
    rows = write_csv_payload()
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_social_security_registration_adapter",
        "source_tables": "BGGL_XZ_JXDJ_ZB,BGGL_XZ_JXDJ",
        "total_rows": rows,
        "header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_XZ_JXDJ_ZB;")),
        "line_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_XZ_JXDJ;")),
        "active_amount_2026": scalar(
            """
            SET NOCOUNT ON;
            SELECT COALESCE(SUM(c.JXGZ),0)
            FROM dbo.BGGL_XZ_JXDJ c
            LEFT JOIN dbo.BGGL_XZ_JXDJ_ZB h ON h.Id = c.ZBID
            WHERE ISNULL(h.DEL,0)=0 AND h.DJZT='2' AND COALESCE(h.ND,c.ND)='2026';
            """
        ),
        "payload_csv": str(OUTPUT_CSV),
        "decision": "legacy_social_security_registration_payload_ready",
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FRESH_DB_LEGACY_SOCIAL_SECURITY_REGISTRATION_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
