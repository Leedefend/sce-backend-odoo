#!/usr/bin/env python3
"""Build replay payloads for legacy user context facts from restored LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts/migration"
DEPARTMENT_CSV = ARTIFACT_DIR / "fresh_db_legacy_department_replay_payload_v1.csv"
PROFILE_CSV = ARTIFACT_DIR / "fresh_db_legacy_user_profile_replay_payload_v1.csv"
ROLE_CSV = ARTIFACT_DIR / "fresh_db_legacy_user_role_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_user_context_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")

DEPARTMENT_FIELDS = [
    "legacy_department_id",
    "name",
    "parent_legacy_department_id",
    "depth",
    "state",
    "identity_path",
    "legacy_project_id",
    "is_company",
    "is_child_company",
    "charge_leader_legacy_user_id",
    "charge_leader_name",
    "note",
]
PROFILE_FIELDS = [
    "legacy_user_id",
    "generated_login",
    "source_login",
    "display_name",
    "phone",
    "email",
    "employee_no",
    "person_state",
    "deleted_flag",
    "locked_flag",
    "is_admin_flag",
    "sex",
    "account_type",
    "user_type",
    "legacy_department_id",
    "department_name",
    "tr_user_id",
    "tr_user_state",
    "tr_user_operator",
    "tr_user_job_number",
    "source_evidence",
]
ROLE_FIELDS = [
    "legacy_assignment_id",
    "legacy_user_id",
    "generated_login",
    "legacy_role_id",
    "role_name",
    "role_source",
    "company_legacy_id",
    "source_table",
    "note",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def run_sql(sql: str) -> str:
    cmd = [
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
    return subprocess.check_output(cmd, text=True)


def parse_rows(raw: str, fields: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(fields):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(fields), "line": line[:500]})
        rows.append(dict(zip(fields, parts)))
    return rows


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def department_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("ID")} AS legacy_department_id,
  {clean_sql("PNAME")} AS name,
  {clean_sql("PARENTID")} AS parent_legacy_department_id,
  {clean_sql("DEPTH")} AS depth,
  {clean_sql("STATE")} AS state,
  {clean_sql("IDENTITY_STR")} AS identity_path,
  {clean_sql("XMID")} AS legacy_project_id,
  {clean_sql("IS_COMPANY")} AS is_company,
  {clean_sql("IS_CHILD_COMPANY")} AS is_child_company,
  {clean_sql("CHARGELEADERID")} AS charge_leader_legacy_user_id,
  {clean_sql("CHARGELEADER")} AS charge_leader_name,
  {clean_sql("'source_table=BASE_ORGANIZATION_DEPARTMENT; other_system_id=' + COALESCE(OTHER_SYSTEM_ID, '') + '; other_system_code=' + COALESCE(OTHER_SYSTEM_CODE, '')")} AS note
FROM dbo.BASE_ORGANIZATION_DEPARTMENT
WHERE NULLIF(LTRIM(RTRIM(ID)), '') IS NOT NULL
ORDER BY ID;
"""
    return parse_rows(run_sql(sql), DEPARTMENT_FIELDS)


def profile_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
WITH tr_ranked AS (
  SELECT *, ROW_NUMBER() OVER (
    PARTITION BY CONVERT(varchar(80), user_operator)
    ORDER BY CASE WHEN ISNULL(user_state, 0) = 1 THEN 0 ELSE 1 END, user_id
  ) AS rn
  FROM dbo.tr_user
)
SELECT
  {clean_sql("u.ID")} AS legacy_user_id,
  {clean_sql("'legacy_' + CONVERT(varchar(max), u.ID)")} AS generated_login,
  {clean_sql("u.USERNAME")} AS source_login,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(u.PERSON_NAME)), ''), u.USERNAME)")} AS display_name,
  {clean_sql("u.PHONE_NUMBER")} AS phone,
  {clean_sql("u.EMAIL")} AS email,
  {clean_sql("u.YGGH")} AS employee_no,
  {clean_sql("u.PERSON_STATE")} AS person_state,
  {clean_sql("u.DEL")} AS deleted_flag,
  {clean_sql("u.ISLOCK")} AS locked_flag,
  {clean_sql("u.ISADMIN")} AS is_admin_flag,
  {clean_sql("u.SEX")} AS sex,
  {clean_sql("u.ZHLX")} AS account_type,
  {clean_sql("u.USER_TYPE")} AS user_type,
  {clean_sql("t.user_departmentid")} AS legacy_department_id,
  {clean_sql("d.PNAME")} AS department_name,
  {clean_sql("t.user_id")} AS tr_user_id,
  {clean_sql("t.user_state")} AS tr_user_state,
  {clean_sql("t.user_operator")} AS tr_user_operator,
  {clean_sql("t.user_jobNumber")} AS tr_user_job_number,
  {clean_sql("'source_table=BASE_SYSTEM_USER; tr_user_match=user_operator; password_hash_present=' + CASE WHEN NULLIF(LTRIM(RTRIM(COALESCE(u.PASSWORD_MD5, u.PASSWORD))), '') IS NULL THEN '0' ELSE '1' END + '; mobile=' + COALESCE(u.PHONE_NUMBER, '')")} AS source_evidence
FROM dbo.BASE_SYSTEM_USER u
LEFT JOIN tr_ranked t ON CONVERT(varchar(80), t.user_operator) = CONVERT(varchar(80), u.USERNAME) AND t.rn = 1
LEFT JOIN dbo.BASE_ORGANIZATION_DEPARTMENT d ON CONVERT(varchar(80), d.ID) = CONVERT(varchar(80), t.user_departmentid)
WHERE NULLIF(LTRIM(RTRIM(u.ID)), '') IS NOT NULL
ORDER BY u.ID;
"""
    return parse_rows(run_sql(sql), PROFILE_FIELDS)


def role_rows() -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("CONCAT('base_system_user_role:', r.ID)")} AS legacy_assignment_id,
  {clean_sql("r.USERID")} AS legacy_user_id,
  {clean_sql("CONCAT('legacy_', r.USERID)")} AS generated_login,
  {clean_sql("r.ROLEID")} AS legacy_role_id,
  {clean_sql("role.ROLE_NAME")} AS role_name,
  'base_system_role' AS role_source,
  '' AS company_legacy_id,
  'BASE_SYSTEM_USER_ROLE' AS source_table,
  {clean_sql("CONCAT('source_table=BASE_SYSTEM_USER_ROLE; user_name=', COALESCE(r.USERNAME, ''))")} AS note
FROM dbo.BASE_SYSTEM_USER_ROLE r
LEFT JOIN dbo.BASE_SYSTEM_ROLE role ON CONVERT(varchar(80), role.ID) = CONVERT(varchar(80), r.ROLEID)
WHERE NULLIF(LTRIM(RTRIM(r.ID)), '') IS NOT NULL
UNION ALL
SELECT
  {clean_sql("CONCAT('tr_role_to_user:', r.Id)")} AS legacy_assignment_id,
  {clean_sql("r.userId")} AS legacy_user_id,
  {clean_sql("CONCAT('legacy_', r.userId)")} AS generated_login,
  {clean_sql("r.roleId")} AS legacy_role_id,
  {clean_sql("role.role_name")} AS role_name,
  'tr_role' AS role_source,
  {clean_sql("r.GSID")} AS company_legacy_id,
  'tr_RoleToUser' AS source_table,
  {clean_sql("CONCAT('source_table=tr_RoleToUser; company_legacy_id=', COALESCE(CONVERT(varchar(max), r.GSID), ''))")} AS note
FROM dbo.tr_RoleToUser r
LEFT JOIN dbo.ts_role role ON CONVERT(varchar(80), role.role_id) = CONVERT(varchar(80), r.roleId)
WHERE NULLIF(LTRIM(RTRIM(r.Id)), '') IS NOT NULL
ORDER BY source_table, legacy_assignment_id;
"""
    return parse_rows(run_sql(sql), ROLE_FIELDS)


def main() -> int:
    departments = department_rows()
    profiles = profile_rows()
    roles = role_rows()
    write_csv(DEPARTMENT_CSV, DEPARTMENT_FIELDS, departments)
    write_csv(PROFILE_CSV, PROFILE_FIELDS, profiles)
    write_csv(ROLE_CSV, ROLE_FIELDS, roles)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_user_context_replay_adapter",
        "department_rows": len(departments),
        "profile_rows": len(profiles),
        "role_rows": len(roles),
        "department_csv": str(DEPARTMENT_CSV),
        "profile_csv": str(PROFILE_CSV),
        "role_csv": str(ROLE_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_LEGACY_USER_CONTEXT_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
