#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
from pathlib import Path


OUTPUT_JSON = Path("artifacts/migration/legacy_db_full_rebuild_blueprint_v1.json")

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

CORE_TABLES = [
    "BASE_SYSTEM_PROJECT",
    "T_System_XMGL",
    "BASE_SYSTEM_PROJECT_USER",
    "T_ProjectContract_Out",
    "C_ZFSQGL",
    "C_JFHKLR",
    "T_Base_CooperatCompany",
    "T_Base_SupplierInfo",
    "T_FK_Supplier",
    "BASE_SYSTEM_FILE",
    "T_BILL_FILE",
    "BASE_SYSTEM_MENU",
    "ts_function",
]


def run_sql(sql: str) -> list[list[str]]:
    proc = subprocess.run(
        [*SQLCMD, "-h", "-1", "-Q", f"SET NOCOUNT ON; {sql}"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows = []
    for line in proc.stdout.splitlines():
        line = line.rstrip("\r\n")
        if not line or line.startswith("("):
            continue
        rows.append([part.strip() for part in line.split("\t")])
    return rows


def run_int(sql: str) -> int:
    rows = run_sql(sql)
    if not rows or not rows[-1]:
        return 0
    return int(rows[-1][0] or 0)


def table_inventory() -> list[dict[str, object]]:
    sql = """
    SELECT TOP 120
        s.name AS schema_name,
        t.name AS table_name,
        SUM(p.rows) AS row_count
    FROM sys.tables t
    JOIN sys.schemas s ON s.schema_id = t.schema_id
    JOIN sys.partitions p ON p.object_id = t.object_id AND p.index_id IN (0, 1)
    GROUP BY s.name, t.name
    ORDER BY SUM(p.rows) DESC, t.name;
    """
    return [
        {"schema": row[0], "table": row[1], "rows": int(row[2] or 0)}
        for row in run_sql(sql)
        if len(row) >= 3
    ]


def column_inventory() -> dict[str, list[dict[str, object]]]:
    result = {}
    for table in CORE_TABLES:
        sql = f"""
        SELECT
            c.column_id,
            c.name,
            ty.name,
            c.max_length,
            c.is_nullable
        FROM sys.columns c
        JOIN sys.types ty ON ty.user_type_id = c.user_type_id
        WHERE c.object_id = OBJECT_ID('dbo.{table}')
        ORDER BY c.column_id;
        """
        result[table] = [
            {
                "ordinal": int(row[0]),
                "name": row[1],
                "type": row[2],
                "max_length": int(row[3]),
                "nullable": row[4] == "1",
            }
            for row in run_sql(sql)
            if len(row) >= 5
        ]
    return result


def metrics() -> dict[str, int]:
    queries = {
        "project_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT;",
        "project_deleted_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT WHERE CONVERT(nvarchar(20), DEL) = '1';",
        "project_other_system_id_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), OTHER_SYSTEM_ID))), '') IS NOT NULL;",
        "legacy_project_ext_rows": "SELECT COUNT(*) FROM dbo.T_System_XMGL;",
        "project_user_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT_USER;",
        "contract_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out;",
        "contract_deleted_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out WHERE CONVERT(nvarchar(20), DEL) = '1';",
        "contract_project_match_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out c WHERE EXISTS (SELECT 1 FROM dbo.BASE_SYSTEM_PROJECT p WHERE CONVERT(nvarchar(100), p.ID) = CONVERT(nvarchar(100), c.XMID));",
        "contract_distinct_project_ids": "SELECT COUNT(DISTINCT XMID) FROM dbo.T_ProjectContract_Out WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), XMID))), '') IS NOT NULL;",
        "company_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany;",
        "company_deleted_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany WHERE CONVERT(nvarchar(20), DEL) = '1';",
        "company_credit_code_rows": "SELECT COUNT(*) FROM dbo.T_Base_CooperatCompany WHERE NULLIF(LTRIM(RTRIM(TYSHXYDM)), '') IS NOT NULL;",
        "supplier_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo;",
        "supplier_bank_rows": "SELECT COUNT(*) FROM dbo.T_Base_SupplierInfo WHERE NULLIF(LTRIM(RTRIM(f_BankCardNumber)), '') IS NOT NULL;",
        "receipt_rows": "SELECT COUNT(*) FROM dbo.C_JFHKLR;",
        "receipt_contract_linked_rows": "SELECT COUNT(*) FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL;",
        "receipt_single_counterparty_contracts": "SELECT COUNT(*) FROM (SELECT SGHTID FROM dbo.C_JFHKLR WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), SGHTID))), '') IS NOT NULL GROUP BY SGHTID HAVING COUNT(DISTINCT WLDWID) = 1) x;",
        "file_index_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_FILE;",
        "legacy_file_index_rows": "SELECT COUNT(*) FROM dbo.T_BILL_FILE;",
        "menu_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_MENU;",
        "function_rows": "SELECT COUNT(*) FROM dbo.ts_function;",
    }
    result = {}
    for key, sql in queries.items():
        result[key] = run_int(sql)
    return result


def main() -> int:
    result = {
        "status": "PASS",
        "mode": "legacy_db_readonly_full_rebuild_blueprint_probe",
        "database": "LegacyDb",
        "top_tables": table_inventory(),
        "core_table_columns": column_inventory(),
        "metrics": metrics(),
        "recommended_rebuild_order": [
            "platform baseline and dictionaries",
            "partner primary source from T_Base_CooperatCompany",
            "partner supplemental source from T_Base_SupplierInfo",
            "project skeleton from BASE_SYSTEM_PROJECT and T_System_XMGL",
            "project membership from BASE_SYSTEM_PROJECT_USER",
            "contract skeleton from T_ProjectContract_Out after partner/project readiness",
            "contract counterparty linking from strong evidence and confirmed mappings",
            "receipt and request slices after contract readiness",
            "attachments after business record identities are materialized",
            "menus/functions only as legacy reference, not direct import",
        ],
        "decision": "full rebuild blueprint ready; no production write permitted yet",
        "next_step": "promote partner rebuild importer design under repeatable pipeline gates",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        "LEGACY_DB_FULL_REBUILD_BLUEPRINT="
        + json.dumps(
            {
                "status": result["status"],
                "table_inventory_count": len(result["top_tables"]),
                "core_table_count": len(result["core_table_columns"]),
                "metrics": result["metrics"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
