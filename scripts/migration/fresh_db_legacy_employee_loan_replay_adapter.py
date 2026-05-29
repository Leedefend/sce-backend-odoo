#!/usr/bin/env python3
"""Build replay payload for legacy employee loan request/repayment rows."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "migration"
OUTPUT_CSV = ARTIFACT_DIR / "fresh_db_legacy_employee_loan_replay_payload_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "fresh_db_legacy_employee_loan_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_HOST = os.getenv("LEGACY_MSSQL_HOST", "")
SQL_PORT = os.getenv("LEGACY_MSSQL_PORT", "1433")
SQL_USER = os.getenv("LEGACY_MSSQL_USER", "sa")
SQLCMD_DOCKER_IMAGE = os.getenv("LEGACY_SQLCMD_DOCKER_IMAGE", "mcr.microsoft.com/mssql-tools")
SQLCMD_DOCKER_BIN = os.getenv("LEGACY_SQLCMD_DOCKER_BIN", "/opt/mssql-tools/bin/sqlcmd")

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_pid",
    "loan_type",
    "direction",
    "document_no",
    "document_date",
    "due_date",
    "legacy_state",
    "project_legacy_id",
    "project_name",
    "counterparty_legacy_id",
    "counterparty_name",
    "amount",
    "amount_field",
    "purpose",
    "source_type_label",
    "source_extra_ref",
    "source_extra_label",
    "account_legacy_id",
    "account_name",
    "creator_legacy_user_id",
    "creator_name",
    "created_time",
    "modifier_legacy_user_id",
    "modifier_name",
    "modified_time",
    "note",
]


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), "
        f"{field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


def sqlcmd(sql: str) -> list[str]:
    if SQL_HOST:
        server = f"tcp:{SQL_HOST},{SQL_PORT}"
        if Path(SQLCMD).exists():
            return [
                SQLCMD,
                "-S",
                server,
                "-U",
                SQL_USER,
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
        return [
            "docker",
            "run",
            "--rm",
            SQLCMD_DOCKER_IMAGE,
            SQLCMD_DOCKER_BIN,
            "-S",
            server,
            "-U",
            SQL_USER,
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
  'BGGL_JHK_JKSQ' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("pid")} AS legacy_pid,
  'borrowing_request' AS loan_type,
  'borrowed_fund' AS direction,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), SQSJ, 23)")} AS document_date,
  {clean_sql("CONVERT(varchar(10), YJGHSJ, 23)")} AS due_date,
  {clean_sql("DJZT")} AS legacy_state,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(WLDWID, ''), NULLIF(SKR, ''), NULLIF(SQRID, ''))")} AS counterparty_legacy_id,
  {clean_sql("COALESCE(NULLIF(WLDWMC, ''), NULLIF(SKR, ''), NULLIF(SQR, ''))")} AS counterparty_name,
  {clean_sql("COALESCE(NULLIF(SJPFJE, 0), NULLIF(SQJE, 0), NULLIF(JKJE, 0), 0)")} AS amount,
  'SJPFJE/SQJE/JKJE' AS amount_field,
  {clean_sql("ZYZJSYAP")} AS purpose,
  {clean_sql("COALESCE(NULLIF(FKFSMC, ''), NULLIF(FX, ''), NULLIF(SX, ''))")} AS source_type_label,
  {clean_sql("SQBM")} AS source_extra_ref,
  {clean_sql("COALESCE(NULLIF(SFYSN, ''), NULLIF(YS, ''))")} AS source_extra_label,
  {clean_sql("ZKZHID")} AS account_legacy_id,
  {clean_sql("ZKZH")} AS account_name,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  {clean_sql("CONVERT(varchar(19), LRSJ, 120)")} AS created_time,
  {clean_sql("XGRID")} AS modifier_legacy_user_id,
  {clean_sql("XGR")} AS modifier_name,
  {clean_sql("CONVERT(varchar(19), XGSJ, 120)")} AS modified_time,
  {clean_sql("COALESCE(NULLIF(BZ, ''), NULLIF(FJ, ''), NULLIF(LJJKQK, ''))")} AS note
FROM dbo.BGGL_JHK_JKSQ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(COALESCE(NULLIF(SJPFJE, 0), NULLIF(SQJE, 0), NULLIF(JKJE, 0), 0), 0) <> 0
UNION ALL
SELECT
  'BGGL_JHK_HKDJ' AS source_table,
  {clean_sql("Id")} AS legacy_record_id,
  {clean_sql("pid")} AS legacy_pid,
  'borrowing_request' AS loan_type,
  'borrowed_fund' AS direction,
  {clean_sql("DJBH")} AS document_no,
  {clean_sql("CONVERT(varchar(10), HKRQ, 23)")} AS document_date,
  '' AS due_date,
  {clean_sql("DJZT")} AS legacy_state,
  {clean_sql("XMID")} AS project_legacy_id,
  {clean_sql("XMMC")} AS project_name,
  {clean_sql("COALESCE(NULLIF(WLDWID, ''), NULLIF(PersonId, ''))")} AS counterparty_legacy_id,
  {clean_sql("COALESCE(NULLIF(WLDWMC, ''), NULLIF(HKR, ''), NULLIF(SQR, ''))")} AS counterparty_name,
  {clean_sql("HKJE")} AS amount,
  'HKJE' AS amount_field,
  {clean_sql("ZYZJSYAP")} AS purpose,
  '还款登记' AS source_type_label,
  {clean_sql("SQBM")} AS source_extra_ref,
  {clean_sql("SFYSN")} AS source_extra_label,
  {clean_sql("HKZHID")} AS account_legacy_id,
  {clean_sql("HKZH")} AS account_name,
  {clean_sql("LRRID")} AS creator_legacy_user_id,
  {clean_sql("LRR")} AS creator_name,
  {clean_sql("CONVERT(varchar(19), LRSJ, 120)")} AS created_time,
  {clean_sql("XGRID")} AS modifier_legacy_user_id,
  {clean_sql("XGR")} AS modifier_name,
  {clean_sql("CONVERT(varchar(19), XGSJ, 120)")} AS modified_time,
  {clean_sql("FJ")} AS note
FROM dbo.BGGL_JHK_HKDJ
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
  AND ISNULL(DEL, 0) = 0
  AND ISNULL(HKJE, 0) <> 0
ORDER BY source_table, document_date, legacy_record_id;
"""


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    by_source: dict[str, int] = {}
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
                by_source[parts[0]] = by_source.get(parts[0], 0) + 1
        return_code = proc.wait()
    if return_code != 0:
        raise RuntimeError({"sqlcmd_failed": return_code})
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_employee_loan_replay_adapter",
        "rows": count,
        "by_source": by_source,
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print("LEGACY_EMPLOYEE_LOAN_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
