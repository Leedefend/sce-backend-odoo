#!/usr/bin/env python3
"""Read-only legacy SQL Server probe for user and tax migration facts."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


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


class LegacyProbeError(Exception):
    pass


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


def scalar_int(sql: str) -> int:
    rows = run_sql(sql)
    if not rows or not rows[-1]:
        return 0
    value = rows[-1][0]
    return int(float(value)) if value else 0


def rows_as_dicts(sql: str, columns: list[str]) -> list[dict[str, str]]:
    rows = run_sql(sql)
    return [{columns[index]: row[index] if index < len(row) else "" for index in range(len(columns))} for row in rows]


def probe_users() -> dict[str, Any]:
    summary_queries = {
        "base_user_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER;",
        "base_user_active_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER WHERE ISNULL(CONVERT(nvarchar(20), DEL), '0') = '0';",
        "base_user_deleted_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER WHERE CONVERT(nvarchar(20), DEL) = '1';",
        "base_user_admin_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER WHERE ISNULL(ISADMIN, 0) = 1;",
        "base_user_distinct_ids": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), ID))), '')) FROM dbo.BASE_SYSTEM_USER;",
        "base_user_distinct_pid": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), PID))), '')) FROM dbo.BASE_SYSTEM_USER;",
        "base_user_distinct_username": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), USERNAME))), '')) FROM dbo.BASE_SYSTEM_USER;",
        "base_user_missing_username_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), USERNAME))), '') IS NULL;",
        "base_user_missing_person_name_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_USER WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(200), PERSON_NAME))), '') IS NULL;",
        "project_member_rows": "SELECT COUNT(*) FROM dbo.BASE_SYSTEM_PROJECT_USER;",
        "project_member_distinct_user_refs": "SELECT COUNT(DISTINCT NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), USERID))), '')) FROM dbo.BASE_SYSTEM_PROJECT_USER;",
        "project_member_userid_matches_base_user_id_rows": """
            SELECT COUNT(*)
            FROM dbo.BASE_SYSTEM_PROJECT_USER m
            WHERE EXISTS (
              SELECT 1 FROM dbo.BASE_SYSTEM_USER u
              WHERE LTRIM(RTRIM(CONVERT(nvarchar(100), u.ID))) = LTRIM(RTRIM(CONVERT(nvarchar(100), m.USERID)))
            );
        """,
        "project_member_userid_matches_base_user_pid_rows": """
            SELECT COUNT(*)
            FROM dbo.BASE_SYSTEM_PROJECT_USER m
            WHERE EXISTS (
              SELECT 1 FROM dbo.BASE_SYSTEM_USER u
              WHERE LTRIM(RTRIM(CONVERT(nvarchar(100), u.PID))) = LTRIM(RTRIM(CONVERT(nvarchar(100), m.USERID)))
            );
        """,
        "project_member_distinct_user_refs_match_base_user_id": """
            SELECT COUNT(*)
            FROM (
              SELECT DISTINCT LTRIM(RTRIM(CONVERT(nvarchar(100), USERID))) AS USERID
              FROM dbo.BASE_SYSTEM_PROJECT_USER
              WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), USERID))), '') IS NOT NULL
            ) m
            WHERE EXISTS (
              SELECT 1 FROM dbo.BASE_SYSTEM_USER u
              WHERE LTRIM(RTRIM(CONVERT(nvarchar(100), u.ID))) = m.USERID
            );
        """,
        "project_member_distinct_user_refs_match_base_user_pid": """
            SELECT COUNT(*)
            FROM (
              SELECT DISTINCT LTRIM(RTRIM(CONVERT(nvarchar(100), USERID))) AS USERID
              FROM dbo.BASE_SYSTEM_PROJECT_USER
              WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), USERID))), '') IS NOT NULL
            ) m
            WHERE EXISTS (
              SELECT 1 FROM dbo.BASE_SYSTEM_USER u
              WHERE LTRIM(RTRIM(CONVERT(nvarchar(100), u.PID))) = m.USERID
            );
        """,
    }
    summary = {key: scalar_int(sql) for key, sql in summary_queries.items()}
    samples = rows_as_dicts(
        """
        SELECT TOP 20
          CONVERT(nvarchar(100), ID) AS legacy_user_id,
          CONVERT(nvarchar(100), PID) AS legacy_user_pid,
          CONVERT(nvarchar(200), USERNAME) AS login,
          CONVERT(nvarchar(200), PERSON_NAME) AS name,
          CONVERT(nvarchar(100), PHONE_NUMBER) AS phone,
          CONVERT(nvarchar(200), EMAIL) AS email,
          CONVERT(nvarchar(20), DEL) AS deleted,
          CONVERT(nvarchar(20), ISADMIN) AS is_admin
        FROM dbo.BASE_SYSTEM_USER
        ORDER BY PID;
        """,
        ["legacy_user_id", "legacy_user_pid", "login", "name", "phone", "email", "deleted", "is_admin"],
    )
    unmatched_member_refs = rows_as_dicts(
        """
        SELECT TOP 20 m.USERID, COUNT(*) AS rows
        FROM dbo.BASE_SYSTEM_PROJECT_USER m
        WHERE NULLIF(LTRIM(RTRIM(CONVERT(nvarchar(100), m.USERID))), '') IS NOT NULL
          AND NOT EXISTS (
            SELECT 1 FROM dbo.BASE_SYSTEM_USER u
            WHERE LTRIM(RTRIM(CONVERT(nvarchar(100), u.ID))) = LTRIM(RTRIM(CONVERT(nvarchar(100), m.USERID)))
               OR LTRIM(RTRIM(CONVERT(nvarchar(100), u.PID))) = LTRIM(RTRIM(CONVERT(nvarchar(100), m.USERID)))
          )
        GROUP BY m.USERID
        ORDER BY COUNT(*) DESC;
        """,
        ["legacy_user_ref", "rows"],
    )
    return {
        "summary": summary,
        "samples": samples,
        "unmatched_project_member_user_refs_sample": unmatched_member_refs,
        "asset_decision": {
            "can_generate_user_asset_from_base_system_user": summary["base_user_rows"] > 0
            and summary["base_user_distinct_ids"] == summary["base_user_rows"]
            and summary["base_user_missing_username_rows"] == 0
            and summary["base_user_missing_person_name_rows"] == 0,
            "identity_field": "BASE_SYSTEM_USER.ID",
            "login_field": "USERNAME",
            "name_field": "PERSON_NAME",
            "defer_authority_fields": ["groups_id", "sc_role_profile", "company_ids", "department", "post"],
        },
    }


def probe_tax() -> dict[str, Any]:
    summary_queries = {
        "contract_rows": "SELECT COUNT(*) FROM dbo.T_ProjectContract_Out;",
        "contract_tax_field_nonempty_rows": """
            SELECT COUNT(*) FROM dbo.T_ProjectContract_Out
            WHERE D_XXJZ_FPSLV IS NOT NULL;
        """,
        "contract_direction_out_rows": """
            SELECT COUNT(*)
            FROM dbo.T_ProjectContract_Out
            WHERE LTRIM(RTRIM(CONVERT(nvarchar(200), CBF))) IN (N'四川保盛建设集团有限公司', N'My Company')
              AND LTRIM(RTRIM(CONVERT(nvarchar(200), FBF))) NOT IN (N'四川保盛建设集团有限公司', N'My Company', N'');
        """,
        "contract_direction_in_rows": """
            SELECT COUNT(*)
            FROM dbo.T_ProjectContract_Out
            WHERE LTRIM(RTRIM(CONVERT(nvarchar(200), FBF))) IN (N'四川保盛建设集团有限公司', N'My Company')
              AND LTRIM(RTRIM(CONVERT(nvarchar(200), CBF))) NOT IN (N'四川保盛建设集团有限公司', N'My Company', N'');
        """,
        "gysht_info_rows": "SELECT COUNT(*) FROM dbo.T_GYSHT_INFO;",
        "gysht_info_slv_nonempty_rows": "SELECT COUNT(*) FROM dbo.T_GYSHT_INFO WHERE SLV IS NOT NULL;",
        "gysht_info_purchase_13_rows": "SELECT COUNT(*) FROM dbo.T_GYSHT_INFO WHERE SLV = 0.13;",
        "gysht_info_sale_9_rows": "SELECT COUNT(*) FROM dbo.T_GYSHT_INFO WHERE SLV = 0.09;",
        "gysht_info_slv_zero_rows": "SELECT COUNT(*) FROM dbo.T_GYSHT_INFO WHERE SLV = 0;",
    }
    summary = {key: scalar_int(sql) for key, sql in summary_queries.items()}
    contract_tax_distribution = rows_as_dicts(
        """
        SELECT
          COALESCE(CONVERT(nvarchar(100), D_XXJZ_FPSLV), N'<NULL>') AS rate,
          COUNT(*) AS rows
        FROM dbo.T_ProjectContract_Out
        GROUP BY D_XXJZ_FPSLV
        ORDER BY COUNT(*) DESC;
        """,
        ["rate", "rows"],
    )
    supplier_contract_tax_distribution = rows_as_dicts(
        """
        SELECT TOP 20
          COALESCE(CONVERT(nvarchar(100), SLV), N'<NULL>') AS rate,
          COUNT(*) AS rows
        FROM dbo.T_GYSHT_INFO
        GROUP BY SLV
        ORDER BY COUNT(*) DESC;
        """,
        ["rate", "rows"],
    )
    return {
        "summary": summary,
        "contract_tax_distribution": contract_tax_distribution,
        "supplier_contract_tax_distribution": supplier_contract_tax_distribution,
        "asset_decision": {
            "contract_row_level_tax_available": summary["contract_tax_field_nonempty_rows"] > 0,
            "can_generate_default_tax_seed_from_legacy_context": summary["gysht_info_purchase_13_rows"] > 0
            or summary["gysht_info_sale_9_rows"] > 0,
            "contract_tax_policy": "use_target_model_default_by_contract_type_after_tax_seed",
            "default_tax_seed_candidates": [
                {"xml_id": "legacy_tax_sale_9", "name": "销项VAT 9%", "amount": 9.0, "type_tax_use": "sale"},
                {"xml_id": "legacy_tax_purchase_13", "name": "进项VAT 13%", "amount": 13.0, "type_tax_use": "purchase"},
            ],
            "row_level_tax_reason": "T_ProjectContract_Out.D_XXJZ_FPSLV is NULL for all contract rows; do not fabricate per-row tax.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe legacy user and tax facts read-only.")
    parser.add_argument("--out", default=".runtime_artifacts/migration_assets/legacy_user_tax_fact_probe_v1.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = {
            "status": "PASS",
            "mode": "legacy_user_tax_fact_probe",
            "database": "LegacyDb",
            "legacy_db_writes": 0,
            "target_db_writes": 0,
            "odoo_shell": False,
            "user": probe_users(),
            "tax": probe_tax(),
            "next_assets": [
                "user_sc_v1",
                "tax_policy_or_seed_v1",
            ],
        }
    except (subprocess.CalledProcessError, LegacyProbeError, ValueError) as exc:
        payload = {
            "status": "FAIL",
            "error": str(exc),
            "legacy_db_writes": 0,
            "target_db_writes": 0,
            "odoo_shell": False,
        }
        print("LEGACY_USER_TAX_FACT_PROBE=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "LEGACY_USER_TAX_FACT_PROBE="
        + json.dumps(
            {
                "status": payload["status"],
                "base_user_rows": payload["user"]["summary"]["base_user_rows"],
                "project_member_distinct_user_refs": payload["user"]["summary"]["project_member_distinct_user_refs"],
                "contract_tax_field_nonempty_rows": payload["tax"]["summary"]["contract_tax_field_nonempty_rows"],
                "gysht_info_purchase_13_rows": payload["tax"]["summary"]["gysht_info_purchase_13_rows"],
                "legacy_db_writes": 0,
                "target_db_writes": 0,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
