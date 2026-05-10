#!/usr/bin/env python3
"""Extract legacy outbound project-contract deposit lines with header context."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or REPO_ROOT / "artifacts/migration")
OUTPUT_CSV = ARTIFACT_DIR / "legacy_project_contract_deposit_lines_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "legacy_project_contract_deposit_adapter_result_v1.json"

SOURCE_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SOURCE_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

FIELDS = [
    "legacy_line_id",
    "legacy_rownum",
    "legacy_header_id",
    "document_no",
    "contract_no",
    "contract_title",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "contractor_name",
    "employer_name",
    "construction_unit_name",
    "creator_name",
    "creator_legacy_user_id",
    "created_at",
    "line_deposit_type_id",
    "line_deposit_type",
    "line_amount",
    "payment_method_id",
    "payment_method",
    "return_deadline",
    "legacy_pid",
    "header_raw_payload",
    "line_raw_payload",
]


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def run_sql(sql: str) -> str:
    command = [
        "docker",
        "exec",
        "-i",
        SOURCE_CONTAINER,
        "bash",
        "-lc",
        f"{SQLCMD} -S localhost -U sa -P {shell_quote(SQL_PASSWORD)} -C -d {shell_quote(SOURCE_DATABASE)} -s '\t' -y 0 -Y 0",
    ]
    completed = subprocess.run(command, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode != 0 or "\nMsg " in ("\n" + completed.stdout):
        raise RuntimeError(
            {
                "sqlcmd_failed": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    return completed.stdout


def parse_rows(raw: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in raw.splitlines():
        if not line.strip() or line.startswith("legacy_line_id") or set(line.strip()) <= {"-", "\t"} or line.startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) != len(FIELDS):
            continue
        rows.append(dict(zip(FIELDS, parts)))
    return rows


def main() -> int:
    sql = """
SET NOCOUNT ON;
WITH src AS (
  SELECT
    COALESCE(CONVERT(varchar(100), l.Id), '') AS legacy_line_id,
    COALESCE(CONVERT(varchar(100), ROW_NUMBER() OVER (ORDER BY l.pid, l.Id)), '') AS legacy_rownum,
    COALESCE(CONVERT(varchar(100), l.ZBID), '') AS legacy_header_id,
    COALESCE(CONVERT(varchar(200), h.DJBH), '') AS document_no,
    COALESCE(CONVERT(varchar(200), NULLIF(h.HTBH, '')), COALESCE(CONVERT(varchar(200), NULLIF(h.WBHTBH, '')), '')) AS contract_no,
    COALESCE(CONVERT(varchar(500), NULLIF(h.HTBT, '')), COALESCE(CONVERT(varchar(500), NULLIF(h.f_XMMC, '')), '')) AS contract_title,
    COALESCE(CONVERT(varchar(100), h.DJZT), '') AS document_state,
    COALESCE(CONVERT(varchar(20), h.DEL), '') AS deleted_flag,
    COALESCE(CONVERT(varchar(100), h.XMID), '') AS project_legacy_id,
    COALESCE(CONVERT(varchar(500), h.f_XMMC), '') AS project_name,
    COALESCE(CONVERT(varchar(500), h.CBF), '') AS contractor_name,
    COALESCE(CONVERT(varchar(500), h.FBF), '') AS employer_name,
    COALESCE(CONVERT(varchar(500), h.f_JSDW), '') AS construction_unit_name,
    COALESCE(CONVERT(varchar(200), NULLIF(h.f_LRR, '')), COALESCE(CONVERT(varchar(200), h.LRR), '')) AS creator_name,
    COALESCE(CONVERT(varchar(100), h.LRRID), '') AS creator_legacy_user_id,
    COALESCE(CONVERT(varchar(30), h.f_LRSJ, 126), COALESCE(CONVERT(varchar(30), h.LRRQ, 126), '')) AS created_at,
    COALESCE(CONVERT(varchar(100), l.BZJLXID), '') AS line_deposit_type_id,
    COALESCE(CONVERT(varchar(200), l.BZJLX), '') AS line_deposit_type,
    COALESCE(CONVERT(varchar(100), l.JE), '') AS line_amount,
    COALESCE(CONVERT(varchar(100), l.JNXSID), '') AS payment_method_id,
    COALESCE(CONVERT(varchar(200), l.JNXS), '') AS payment_method,
    COALESCE(CONVERT(varchar(30), l.THSX, 126), '') AS return_deadline,
    COALESCE(CONVERT(varchar(100), l.pid), '') AS legacy_pid,
    (SELECT h.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS header_raw_payload,
    (SELECT l.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS line_raw_payload
  FROM dbo.T_ProjectContract_Out_CB_BZJ l
  LEFT JOIN dbo.T_ProjectContract_Out h ON h.Id = l.ZBID
)
SELECT * FROM src
ORDER BY document_no, legacy_rownum, legacy_line_id;
"""
    rows = parse_rows(run_sql(sql))
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    amount_total = 0.0
    active_rows = 0
    for row in rows:
        try:
            amount_total += float(row["line_amount"] or 0.0)
        except ValueError:
            pass
        if row["deleted_flag"] not in {"1", "True", "true"}:
            active_rows += 1
    result = {
        "status": "PASS",
        "mode": "legacy_project_contract_deposit_adapter",
        "source": f"{SOURCE_CONTAINER}:{SOURCE_DATABASE}.dbo.T_ProjectContract_Out_CB_BZJ",
        "payload_csv": str(OUTPUT_CSV.relative_to(REPO_ROOT)) if OUTPUT_CSV.is_relative_to(REPO_ROOT) else str(OUTPUT_CSV),
        "rows": len(rows),
        "active_rows": active_rows,
        "amount_total": round(amount_total, 2),
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("LEGACY_PROJECT_CONTRACT_DEPOSIT_ADAPTER=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
