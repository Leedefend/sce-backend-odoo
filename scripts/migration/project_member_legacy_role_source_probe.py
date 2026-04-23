#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


OUTPUT_JSON = Path("artifacts/migration/project_member_legacy_role_source_probe_v1.json")
CANDIDATE_TABLES_CSV = Path("artifacts/migration/project_member_legacy_role_candidate_tables_v1.csv")

SQLCMD = [
    "docker",
    "exec",
    "legacy-sqlserver",
    "/opt/mssql-tools18/bin/sqlcmd",
    "-S",
    "localhost",
    "-U",
    "sa",
    "-P",
    "ChangeThis_Strong_Password_123!",
    "-C",
    "-d",
    "LegacyDb",
    "-s",
    "\t",
    "-W",
]


def run_sql(sql: str) -> list[list[str]]:
    proc = subprocess.run(
        [*SQLCMD, "-h", "-1", "-Q", f"SET NOCOUNT ON; {sql}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[list[str]] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("("):
            continue
        rows.append([part.strip() for part in line.split("\t")])
    return rows


def table_columns(table_name: str) -> list[dict[str, object]]:
    rows = run_sql(
        f"""
        SELECT c.column_id, c.name, ty.name, c.max_length, c.is_nullable
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID(N'dbo.{table_name}')
        ORDER BY c.column_id;
        """
    )
    return [
        {
            "ordinal": int(row[0]),
            "name": row[1],
            "type": row[2],
            "max_length": int(row[3]),
            "nullable": row[4] == "1",
        }
        for row in rows
        if len(row) >= 5
    ]


def scalar_int(sql: str) -> int:
    rows = run_sql(sql)
    return int(rows[-1][0]) if rows and rows[-1] and rows[-1][0] else 0


def role_like_columns() -> list[dict[str, object]]:
    rows = run_sql(
        """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            c.name AS column_name,
            ty.name AS data_type,
            SUM(p.rows) AS row_count
        FROM sys.columns c
        JOIN sys.tables t ON t.object_id = c.object_id
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        WHERE
            UPPER(c.name) LIKE N'%ROLE%'
            OR UPPER(c.name) LIKE N'%POST%'
            OR UPPER(c.name) LIKE N'%DUTY%'
            OR UPPER(c.name) LIKE N'%RESP%'
            OR UPPER(c.name) LIKE N'%GW%'
            OR UPPER(c.name) LIKE N'%ZW%'
            OR c.name LIKE N'%角色%'
            OR c.name LIKE N'%岗位%'
            OR c.name LIKE N'%职责%'
            OR c.name LIKE N'%责任%'
        GROUP BY s.name, t.name, c.name, ty.name
        ORDER BY row_count DESC, t.name, c.name;
        """
    )
    return [
        {
            "schema": row[0],
            "table": row[1],
            "column": row[2],
            "type": row[3],
            "rows": int(row[4] or 0),
        }
        for row in rows
        if len(row) >= 5
    ]


def project_user_like_tables() -> list[dict[str, object]]:
    rows = run_sql(
        """
        SELECT
            s.name AS schema_name,
            t.name AS table_name,
            SUM(p.rows) AS row_count
        FROM sys.tables t
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        WHERE
            UPPER(t.name) LIKE N'%PROJECT%USER%'
            OR UPPER(t.name) LIKE N'%PROJECT%ROLE%'
            OR UPPER(t.name) LIKE N'%PROJECT%MEMBER%'
            OR UPPER(t.name) LIKE N'%XM%USER%'
            OR UPPER(t.name) LIKE N'%XM%RY%'
            OR UPPER(t.name) LIKE N'%XM%GW%'
            OR UPPER(t.name) LIKE N'%ROLE%'
            OR UPPER(t.name) LIKE N'%POST%'
            OR t.name LIKE N'%项目%成员%'
            OR t.name LIKE N'%项目%角色%'
            OR t.name LIKE N'%项目%岗位%'
        GROUP BY s.name, t.name
        ORDER BY row_count DESC, t.name;
        """
    )
    return [
        {"schema": row[0], "table": row[1], "rows": int(row[2] or 0)}
        for row in rows
        if len(row) >= 3
    ]


def project_user_role_triad_candidates() -> list[dict[str, object]]:
    rows = run_sql(
        """
        WITH classified AS (
            SELECT
                s.name AS schema_name,
                t.name AS table_name,
                c.name AS column_name,
                CASE WHEN
                    UPPER(c.name) IN (N'XMID', N'PROJECTID', N'PROJECT_ID', N'SSXMID')
                    OR UPPER(c.name) LIKE N'%PROJECT%'
                    OR c.name LIKE N'%项目%'
                THEN 1 ELSE 0 END AS is_project_col,
                CASE WHEN
                    UPPER(c.name) IN (N'USERID', N'USER_ID', N'RYID', N'YHID')
                    OR UPPER(c.name) LIKE N'%USER%'
                    OR c.name LIKE N'%用户%'
                    OR c.name LIKE N'%人员%'
                    OR c.name LIKE N'%员工%'
                THEN 1 ELSE 0 END AS is_user_col,
                CASE WHEN
                    UPPER(c.name) LIKE N'%ROLE%'
                    OR UPPER(c.name) LIKE N'%POST%'
                    OR UPPER(c.name) LIKE N'%DUTY%'
                    OR UPPER(c.name) LIKE N'%GW%'
                    OR UPPER(c.name) LIKE N'%ZW%'
                    OR c.name LIKE N'%角色%'
                    OR c.name LIKE N'%岗位%'
                    OR c.name LIKE N'%职责%'
                    OR c.name LIKE N'%责任%'
                THEN 1 ELSE 0 END AS is_role_col
            FROM sys.columns c
            JOIN sys.tables t ON t.object_id = c.object_id
            JOIN sys.schemas s ON s.schema_id = t.schema_id
        ),
        table_flags AS (
            SELECT
                schema_name,
                table_name,
                MAX(is_project_col) AS has_project_col,
                MAX(is_user_col) AS has_user_col,
                MAX(is_role_col) AS has_role_col,
                STRING_AGG(CASE WHEN is_project_col = 1 THEN column_name END, N', ') AS project_columns,
                STRING_AGG(CASE WHEN is_user_col = 1 THEN column_name END, N', ') AS user_columns,
                STRING_AGG(CASE WHEN is_role_col = 1 THEN column_name END, N', ') AS role_columns
            FROM classified
            GROUP BY schema_name, table_name
        )
        SELECT
            f.schema_name,
            f.table_name,
            SUM(p.rows) AS row_count,
            f.project_columns,
            f.user_columns,
            f.role_columns
        FROM table_flags f
        JOIN sys.tables t ON t.name = f.table_name
        JOIN sys.schemas s ON s.schema_id = t.schema_id AND s.name = f.schema_name
        JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
        WHERE f.has_project_col = 1 AND f.has_user_col = 1 AND f.has_role_col = 1
        GROUP BY f.schema_name, f.table_name, f.project_columns, f.user_columns, f.role_columns
        ORDER BY row_count DESC, f.table_name;
        """
    )
    return [
        {
            "schema": row[0],
            "table": row[1],
            "rows": int(row[2] or 0),
            "project_columns": row[3],
            "user_columns": row[4],
            "role_columns": row[5],
        }
        for row in rows
        if len(row) >= 6
    ]


def sample_rows(table_name: str, columns: list[str], limit: int = 10) -> list[dict[str, str]]:
    column_sql = ", ".join(f"[{column}]" for column in columns)
    rows = run_sql(f"SELECT TOP {limit} {column_sql} FROM dbo.[{table_name}];")
    return [
        {column: row[index] if index < len(row) else "" for index, column in enumerate(columns)}
        for row in rows
    ]


def choose_column(columns_text: str, preferred: list[str]) -> str:
    columns = [column.strip() for column in (columns_text or "").split(",") if column.strip()]
    by_upper = {column.upper(): column for column in columns}
    for name in preferred:
        if name.upper() in by_upper:
            return by_upper[name.upper()]
    return columns[0] if columns else ""


def triad_coverage(candidates: list[dict[str, object]], member_row_count: int) -> list[dict[str, object]]:
    coverage = []
    for item in candidates:
        if int(item.get("rows") or 0) <= 0:
            continue
        table = str(item["table"])
        project_col = choose_column(str(item.get("project_columns") or ""), ["XMID", "SSXMID", "PROJECTID", "PROJECT_ID"])
        user_col = choose_column(str(item.get("user_columns") or ""), ["USERID", "USER_ID", "Userid", "RYID", "YHID", "Ding_Userid"])
        role_col = choose_column(str(item.get("role_columns") or ""), ["PDUTYNAME", "GZGW", "GW", "ZW", "BMGW", "PDUTYID", "RoleId"])
        if not project_col or not user_col or not role_col:
            continue
        matched = scalar_int(
            f"""
            SELECT COUNT(*)
            FROM dbo.BASE_SYSTEM_PROJECT_USER m
            WHERE EXISTS (
                SELECT 1
                FROM dbo.[{table}] c
                WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), c.[{role_col}]))), '') IS NOT NULL
                  AND LTRIM(RTRIM(CONVERT(nvarchar(200), c.[{project_col}]))) = LTRIM(RTRIM(CONVERT(nvarchar(200), m.XMID)))
                  AND LTRIM(RTRIM(CONVERT(nvarchar(200), c.[{user_col}]))) = LTRIM(RTRIM(CONVERT(nvarchar(200), m.USERID)))
            );
            """
        )
        role_samples = run_sql(
            f"""
            SELECT TOP 12 CONVERT(nvarchar(200), c.[{role_col}]), COUNT(*)
            FROM dbo.[{table}] c
            WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), c.[{role_col}]))), '') IS NOT NULL
            GROUP BY CONVERT(nvarchar(200), c.[{role_col}])
            ORDER BY COUNT(*) DESC;
            """
        )
        coverage.append(
            {
                "schema": item["schema"],
                "table": table,
                "rows": item["rows"],
                "project_column": project_col,
                "user_column": user_col,
                "role_column": role_col,
                "matched_project_member_rows": matched,
                "mapping_rate": round(matched / member_row_count, 6) if member_row_count else 0.0,
                "role_value_samples": [
                    {"value": row[0], "rows": int(row[1] or 0)}
                    for row in role_samples
                    if len(row) >= 2
                ],
            }
        )
    return sorted(coverage, key=lambda row: (-float(row["mapping_rate"]), -int(row["rows"])))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["schema", "table", "rows", "role_like_columns", "columns"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    member_columns = table_columns("BASE_SYSTEM_PROJECT_USER")
    member_row_count = scalar_int("SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT_USER;")
    role_columns = role_like_columns()
    table_candidates = project_user_like_tables()
    triad_candidates = project_user_role_triad_candidates()
    triad_coverage_rows = triad_coverage(triad_candidates, member_row_count)

    role_column_by_table: dict[str, list[str]] = {}
    for item in role_columns:
        key = f"{item['schema']}.{item['table']}"
        role_column_by_table.setdefault(key, []).append(str(item["column"]))

    candidate_rows = []
    for table in table_candidates:
        key = f"{table['schema']}.{table['table']}"
        columns = table_columns(str(table["table"]))
        candidate_rows.append(
            {
                "schema": table["schema"],
                "table": table["table"],
                "rows": table["rows"],
                "role_like_columns": ", ".join(role_column_by_table.get(key, [])),
                "columns": ", ".join(str(column["name"]) for column in columns),
            }
        )
    write_csv(CANDIDATE_TABLES_CSV, candidate_rows)

    member_role_columns = [
        column["name"]
        for column in member_columns
        if str(column["name"]).upper() in {"ROLE", "ROLE_KEY", "PROJECT_ROLE", "PROJECT_ROLE_CODE", "POST", "DUTY", "RESP", "GW", "ZW"}
        or any(token in str(column["name"]) for token in ["角色", "岗位", "职责", "责任"])
    ]
    source_has_authoritative_role = bool(member_role_columns)
    mapping_rate = 0.0 if not source_has_authoritative_role else 1.0

    result = {
        "status": "PASS",
        "mode": "project_member_legacy_db_role_source_probe",
        "database": "LegacyDb",
        "project_member_table": "dbo.BASE_SYSTEM_PROJECT_USER",
        "project_member_rows": member_row_count,
        "project_member_columns": member_columns,
        "project_member_role_like_columns": member_role_columns,
        "source_has_authoritative_role": source_has_authoritative_role,
        "role_mapping_rate_from_member_table": mapping_rate,
        "role_like_columns": role_columns,
        "project_user_like_tables": table_candidates,
        "project_user_role_triad_candidates": triad_candidates,
        "project_user_role_triad_coverage": triad_coverage_rows,
        "candidate_samples": {
            "T_System_RoleAndProject": sample_rows("T_System_RoleAndProject", ["Id", "SJBMC", "SSXMID", "RoleId", "LX"], 10),
            "BASE_SYSTEM_USER_ROLE": sample_rows("BASE_SYSTEM_USER_ROLE", ["ID", "PID", "USERID", "USERNAME", "ROLEID"], 10),
            "BASE_SYSTEM_ROLE": sample_rows("BASE_SYSTEM_ROLE", ["ID", "ROLE_NAME", "ROLE_TYPE", "NOTE"], 10),
            "tr_RoleToUser": sample_rows("tr_RoleToUser", ["Id", "userId", "roleId", "GSID"], 10),
        },
        "candidate_table_csv": str(CANDIDATE_TABLES_CSV),
        "decision": (
            "authoritative_role_source_found"
            if source_has_authoritative_role
            else "no_authoritative_role_source_in_project_member_table"
        ),
        "next_step": (
            "run role-mapping dry-run"
            if source_has_authoritative_role
            else "evaluate neutral membership carrier before default role"
        ),
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "PROJECT_MEMBER_LEGACY_ROLE_SOURCE_PROBE="
        + json.dumps(
            {
                "status": result["status"],
                "project_member_rows": member_row_count,
                "project_member_role_like_columns": member_role_columns,
                "source_has_authoritative_role": source_has_authoritative_role,
                "candidate_tables": len(table_candidates),
                "triad_candidates": len(triad_candidates),
                "best_triad_mapping_rate": triad_coverage_rows[0]["mapping_rate"] if triad_coverage_rows else 0.0,
                "role_like_columns": len(role_columns),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
