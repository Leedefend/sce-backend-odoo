#!/usr/bin/env python3
"""Build replay payload for privacy-restricted legacy salary line facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_salary_line_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_salary_line_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

FIELDS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "legacy_header_pid",
    "source_dataset",
    "document_no",
    "document_state",
    "salary_year",
    "salary_month",
    "period_key",
    "title",
    "project_legacy_id",
    "project_name",
    "scope_legacy_ids",
    "scope_names",
    "person_legacy_id",
    "person_name",
    "department_legacy_id",
    "department_name",
    "position_legacy_id",
    "position_name",
    "id_number",
    "salary_base",
    "cash_amount",
    "social_security",
    "housing_fund",
    "individual_tax",
    "welfare_standard",
    "bonus",
    "deduction",
    "gross_amount",
    "performance_salary",
    "net_salary",
    "calculation_base",
    "overtime_amount",
    "post_allowance",
    "seniority_salary",
    "service_salary",
    "meal_allowance",
    "subsidy",
    "overtime_pay",
    "late_absence_deduction",
    "attendance_deduction",
    "medical_insurance_base",
    "medical_insurance_company",
    "unemployment_insurance",
    "social_security_individual_deduction",
    "social_security_company_deduction",
    "tax_deduction",
    "union_fee",
    "housing_fund_deduction",
    "payer_unit",
    "payment_people_count",
    "header_total_amount",
    "header_payable_amount",
    "header_people_count",
    "company_legacy_id",
    "company_name",
    "department_summary_legacy_id",
    "department_summary",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "attachment_ref",
    "source_note",
    "line_note",
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
  {clean_sql("h.pid")} AS legacy_header_pid,
  {clean_sql("COALESCE(c.SJBMC, h.SJBMC)")} AS source_dataset,
  {clean_sql("h.DJBH")} AS document_no,
  {clean_sql("h.DJZT")} AS document_state,
  {clean_sql("h.NF")} AS salary_year,
  {clean_sql("h.YF")} AS salary_month,
  CASE
    WHEN h.NF IS NULL OR h.YF IS NULL THEN ''
    ELSE CONVERT(varchar(4), h.NF) + '-' + RIGHT('00' + CONVERT(varchar(2), h.YF), 2)
  END AS period_key,
  {clean_sql("h.BT")} AS title,
  {clean_sql("h.XMID")} AS project_legacy_id,
  {clean_sql("h.XMMC")} AS project_name,
  {clean_sql("h.TJFWID")} AS scope_legacy_ids,
  {clean_sql("h.TJFW")} AS scope_names,
  {clean_sql("c.RYID")} AS person_legacy_id,
  {clean_sql("c.XM")} AS person_name,
  {clean_sql("c.BMID")} AS department_legacy_id,
  {clean_sql("c.BM")} AS department_name,
  {clean_sql("c.GWZJID")} AS position_legacy_id,
  {clean_sql("c.GWZJ")} AS position_name,
  {clean_sql("c.SFZHM")} AS id_number,
  {clean_sql("c.DK")} AS salary_base,
  {clean_sql("c.XJ")} AS cash_amount,
  {clean_sql("c.SB")} AS social_security,
  {clean_sql("c.GJJ")} AS housing_fund,
  {clean_sql("c.GS")} AS individual_tax,
  {clean_sql("c.FLBZ")} AS welfare_standard,
  {clean_sql("c.JJ")} AS bonus,
  {clean_sql("c.KK")} AS deduction,
  {clean_sql("c.HJ")} AS gross_amount,
  {clean_sql("c.JXGZ")} AS performance_salary,
  {clean_sql("c.SFGZ")} AS net_salary,
  {clean_sql("c.JXGZJS")} AS calculation_base,
  {clean_sql("c.BSJ")} AS overtime_amount,
  {clean_sql("c.GWJT")} AS post_allowance,
  {clean_sql("c.SLGZ")} AS seniority_salary,
  {clean_sql("c.GLGZ")} AS service_salary,
  {clean_sql("c.ZJBT")} AS meal_allowance,
  {clean_sql("c.BT")} AS subsidy,
  {clean_sql("c.JB")} AS overtime_pay,
  {clean_sql("c.CDZTKG")} AS late_absence_deduction,
  {clean_sql("c.QQKK")} AS attendance_deduction,
  {clean_sql("c.JBYLBX")} AS medical_insurance_base,
  {clean_sql("c.JBYLBX_1")} AS medical_insurance_company,
  {clean_sql("c.SYBXF")} AS unemployment_insurance,
  {clean_sql("c.DKSBGR")} AS social_security_individual_deduction,
  {clean_sql("c.DKSBGS")} AS social_security_company_deduction,
  {clean_sql("c.DKGS")} AS tax_deduction,
  {clean_sql("c.GHJF")} AS union_fee,
  {clean_sql("c.ZFGJJ")} AS housing_fund_deduction,
  {clean_sql("c.D_SCBSJS_FFDW")} AS payer_unit,
  {clean_sql("c.FFRS")} AS payment_people_count,
  {clean_sql("h.ZJE")} AS header_total_amount,
  {clean_sql("h.YFZJE")} AS header_payable_amount,
  {clean_sql("h.FFRS")} AS header_people_count,
  {clean_sql("h.SSGSID")} AS company_legacy_id,
  {clean_sql("h.SSGS")} AS company_name,
  {clean_sql("h.BMID")} AS department_summary_legacy_id,
  {clean_sql("h.BM")} AS department_summary,
  {clean_sql("h.LRRID")} AS creator_legacy_user_id,
  {clean_sql("h.LRR")} AS creator_name,
  COALESCE(CONVERT(varchar(23), h.LRSJ, 121), '') AS created_time,
  {clean_sql("h.XGRID")} AS modifier_legacy_user_id,
  {clean_sql("h.XGR")} AS modifier_name,
  COALESCE(CONVERT(varchar(23), h.XGSJ, 121), '') AS modified_time,
  {clean_sql("h.FJ")} AS attachment_ref,
  {clean_sql("h.SM")} AS source_note,
  {clean_sql("c.BZ")} AS line_note,
  CASE WHEN ISNULL(h.DEL, 0) = 0 THEN '1' ELSE '0' END AS active
FROM dbo.BGGL_XZ_GZ_CB c
LEFT JOIN dbo.BGGL_XZ_GZ h ON h.Id = c.ZBID
WHERE NULLIF(LTRIM(RTRIM(c.Id)), '') IS NOT NULL
ORDER BY h.NF, h.YF, c.Id;
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
        "mode": "fresh_db_legacy_salary_line_replay_adapter",
        "total_rows": rows,
        "header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_XZ_GZ;")),
        "active_header_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_XZ_GZ WHERE ISNULL(DEL,0)=0;")),
        "line_rows": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(*) FROM dbo.BGGL_XZ_GZ_CB;")),
        "people_count": int(scalar("SET NOCOUNT ON; SELECT COUNT_BIG(DISTINCT RYID) FROM dbo.BGGL_XZ_GZ_CB;")),
        "orphan_line_rows": int(
            scalar(
                """
                SET NOCOUNT ON;
                SELECT COUNT_BIG(*)
                FROM dbo.BGGL_XZ_GZ_CB c
                LEFT JOIN dbo.BGGL_XZ_GZ h ON h.Id = c.ZBID
                WHERE h.Id IS NULL;
                """
            )
        ),
        "period_min": scalar(
            "SET NOCOUNT ON; SELECT MIN(CONVERT(varchar(4), NF) + '-' + RIGHT('00' + CONVERT(varchar(2), YF), 2)) FROM dbo.BGGL_XZ_GZ;"
        ),
        "period_max": scalar(
            "SET NOCOUNT ON; SELECT MAX(CONVERT(varchar(4), NF) + '-' + RIGHT('00' + CONVERT(varchar(2), YF), 2)) FROM dbo.BGGL_XZ_GZ;"
        ),
        "gross_amount_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(HJ),0) FROM dbo.BGGL_XZ_GZ_CB;"),
        "net_salary_sum": scalar("SET NOCOUNT ON; SELECT COALESCE(SUM(SFGZ),0) FROM dbo.BGGL_XZ_GZ_CB;"),
        "payload_csv": str(OUTPUT_CSV),
        "privacy_boundary": "restricted_config_admin_only",
        "decision": "legacy_salary_line_payload_ready",
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_SALARY_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
