#!/usr/bin/env python3
"""Extract legacy T_ZL_MachineShift headers for fact carry and projection."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or REPO_ROOT / "artifacts/migration")
OUTPUT_CSV = ARTIFACT_DIR / "legacy_t_zl_machine_shift_headers_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "legacy_t_zl_machine_shift_header_adapter_result_v1.json"

SOURCE_CONTAINER = os.getenv("LEGACY_T_ZL_SOURCE_CONTAINER", "legacy-mssql-restore")
SOURCE_DATABASE = os.getenv("LEGACY_T_ZL_SOURCE_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

FIELDS = [
    "legacy_header_id",
    "document_no",
    "document_state",
    "document_date",
    "project_legacy_id",
    "project_name",
    "supplier_legacy_id",
    "supplier_name",
    "use_org_legacy_id",
    "use_org_name",
    "work_part_legacy_id",
    "work_part",
    "title",
    "creator_legacy_user_id",
    "creator_name",
    "created_at",
    "amount_total",
    "legacy_pid",
    "active",
    "raw_payload",
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
    if completed.returncode != 0:
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
        if not line.strip() or line.startswith("legacy_header_id") or set(line.strip()) <= {"-", "\t"} or line.startswith("("):
            continue
        parts = line.split("\t")
        if len(parts) != len(FIELDS):
            continue
        rows.append(dict(zip(FIELDS, parts)))
    return rows


def main() -> int:
    sql = """
SET NOCOUNT ON;
SELECT
  COALESCE(CONVERT(varchar(100), h.Id), '') AS legacy_header_id,
  COALESCE(CONVERT(varchar(200), h.DJBH), '') AS document_no,
  COALESCE(CONVERT(varchar(100), h.DJZT), '') AS document_state,
  COALESCE(CONVERT(varchar(30), h.DJRQ, 126), COALESCE(CONVERT(varchar(30), h.LRSJ, 126), '')) AS document_date,
  COALESCE(CONVERT(varchar(100), h.XMID), '') AS project_legacy_id,
  COALESCE(CONVERT(varchar(500), h.XMMC), '') AS project_name,
  COALESCE(CONVERT(varchar(100), NULLIF(h.ZLDWID, '')), COALESCE(CONVERT(varchar(100), NULLIF(h.SYDWID, '')), '')) AS supplier_legacy_id,
  COALESCE(CONVERT(varchar(500), NULLIF(h.ZLDW, '')), COALESCE(CONVERT(varchar(500), NULLIF(h.SYDW, '')), '')) AS supplier_name,
  COALESCE(CONVERT(varchar(100), h.SYDWID), '') AS use_org_legacy_id,
  COALESCE(CONVERT(varchar(500), h.SYDW), '') AS use_org_name,
  COALESCE(CONVERT(varchar(100), h.SGBWID), '') AS work_part_legacy_id,
  COALESCE(CONVERT(varchar(500), h.SGBW), '') AS work_part,
  COALESCE(CONVERT(varchar(500), h.BT), '') AS title,
  COALESCE(CONVERT(varchar(100), h.LRRID), '') AS creator_legacy_user_id,
  COALESCE(CONVERT(varchar(200), h.LRR), '') AS creator_name,
  COALESCE(CONVERT(varchar(30), h.LRSJ, 126), '') AS created_at,
  COALESCE(CONVERT(varchar(100), h.D_BQJT_ZJE), '') AS amount_total,
  COALESCE(CONVERT(varchar(100), h.pid), '') AS legacy_pid,
  CASE WHEN h.DEL IS NULL OR CONVERT(varchar(20), h.DEL) IN ('', '0', 'False', 'false') THEN '1' ELSE '0' END AS active,
  (SELECT h.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS raw_payload
FROM dbo.T_ZL_MachineShift h
ORDER BY h.DJRQ, h.DJBH, h.Id;
"""
    rows = parse_rows(run_sql(sql))
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "PASS",
        "mode": "legacy_t_zl_machine_shift_header_adapter",
        "source": f"{SOURCE_CONTAINER}:{SOURCE_DATABASE}.dbo.T_ZL_MachineShift",
        "payload_csv": str(OUTPUT_CSV.relative_to(REPO_ROOT)) if OUTPUT_CSV.is_relative_to(REPO_ROOT) else str(OUTPUT_CSV),
        "header_rows": len(rows),
        "active_rows": sum(1 for row in rows if row["active"] == "1"),
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "LEGACY_T_ZL_MACHINE_SHIFT_HEADER_ADAPTER="
        + json.dumps(
            {
                "status": result["status"],
                "header_rows": result["header_rows"],
                "active_rows": result["active_rows"],
                "payload_csv": result["payload_csv"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
