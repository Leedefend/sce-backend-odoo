#!/usr/bin/env python3
"""Extract legacy A_SCBS material inbound headers for formal projection."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = Path(os.getenv("MIGRATION_ARTIFACT_ROOT") or REPO_ROOT / "artifacts/migration")
OUTPUT_CSV = ARTIFACT_DIR / "legacy_a_scbs_material_inbound_headers_v1.csv"
OUTPUT_JSON = ARTIFACT_DIR / "legacy_a_scbs_material_inbound_adapter_result_v1.json"

SOURCE_CONTAINER = os.getenv("LEGACY_A_SCBS_SOURCE_CONTAINER", "legacy-mssql-restore")
SOURCE_DATABASE = os.getenv("LEGACY_A_SCBS_SOURCE_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

FIELDS = [
    "legacy_header_id",
    "document_no",
    "document_date",
    "project_legacy_id",
    "project_name",
    "supplier_legacy_id",
    "supplier_name",
    "keeper_name",
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
        row = dict(zip(FIELDS, parts))
        rows.append(row)
    return rows


def main() -> int:
    sql = """
SET NOCOUNT ON;
SELECT
  CONVERT(varchar(100), h.Id) AS legacy_header_id,
  COALESCE(CONVERT(varchar(200), h.DJBH), '') AS document_no,
  COALESCE(CONVERT(varchar(30), h.DCRQ, 126), '') AS document_date,
  COALESCE(CONVERT(varchar(100), h.XMID), '') AS project_legacy_id,
  COALESCE(CONVERT(varchar(500), h.XMMC), '') AS project_name,
  COALESCE(CONVERT(varchar(100), h.GYSID), '') AS supplier_legacy_id,
  COALESCE(CONVERT(varchar(500), h.GYS), '') AS supplier_name,
  COALESCE(CONVERT(varchar(200), h.TXR), '') AS keeper_name,
  COALESCE(CONVERT(varchar(100), h.LRRID), '') AS creator_legacy_user_id,
  COALESCE(CONVERT(varchar(200), h.LRR), '') AS creator_name,
  COALESCE(CONVERT(varchar(30), h.LRSJ, 126), '') AS created_at,
  COALESCE(CONVERT(varchar(100), h.JE), '') AS amount_total,
  COALESCE(CONVERT(varchar(100), h.pid), '') AS legacy_pid,
  CASE WHEN h.DEL IS NULL OR CONVERT(varchar(20), h.DEL) IN ('', '0', 'False', 'false') THEN '1' ELSE '0' END AS active,
  (SELECT h.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS raw_payload
FROM dbo.A_SCBS_CLRKD h
ORDER BY h.DCRQ, h.DJBH, h.Id;
"""
    rows = parse_rows(run_sql(sql))
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "status": "PASS",
        "mode": "legacy_a_scbs_material_inbound_adapter",
        "source": f"{SOURCE_CONTAINER}:{SOURCE_DATABASE}.dbo.A_SCBS_CLRKD",
        "payload_csv": str(OUTPUT_CSV.relative_to(REPO_ROOT)) if OUTPUT_CSV.is_relative_to(REPO_ROOT) else str(OUTPUT_CSV),
        "header_rows": len(rows),
        "active_rows": sum(1 for row in rows if row["active"] == "1"),
        "amount_total": round(sum(float(row["amount_total"] or 0) for row in rows), 2),
    }
    OUTPUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "LEGACY_A_SCBS_MATERIAL_INBOUND_ADAPTER="
        + json.dumps(
            {
                "status": result["status"],
                "header_rows": result["header_rows"],
                "active_rows": result["active_rows"],
                "amount_total": result["amount_total"],
                "payload_csv": result["payload_csv"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
