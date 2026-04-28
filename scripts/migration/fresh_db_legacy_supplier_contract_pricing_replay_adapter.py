#!/usr/bin/env python3
"""Build replay payload for legacy supplier contract pricing facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_supplier_contract_pricing_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")

FIELDS = [
    "legacy_contract_id",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "pricing_method_legacy_id",
    "pricing_method_text",
    "amount_total",
    "import_batch",
]


def clean_sql(field: str) -> str:
    return (
        "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), "
        + field
        + "), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    )


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


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


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean_sql("g.Id")} AS legacy_contract_id,
  {clean_sql("g.DJZT")} AS document_state,
  CAST(ISNULL(g.DEL, 0) AS varchar(20)) AS deleted_flag,
  {clean_sql("g.XMID")} AS project_legacy_id,
  {clean_sql("p.XMMC")} AS project_name,
  {clean_sql("g.f_GYSID")} AS partner_legacy_id,
  {clean_sql("g.f_GYSName")} AS partner_name,
  {clean_sql("g.JJFSID")} AS pricing_method_legacy_id,
  {clean_sql("g.JJFSTEXT")} AS pricing_method_text,
  CAST(ISNULL(g.ZJE, 0) AS varchar(50)) AS amount_total,
  'legacy_supplier_contract_pricing_v1' AS import_batch
FROM dbo.T_GYSHT_INFO g
LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID = g.XMID
WHERE ISNULL(g.DJZT, '0') = '2'
  AND ISNULL(g.DEL, 0) = 0;
"""
    rows: list[dict[str, str]] = []
    for raw_line in run_sql(sql).splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("("):
            continue
        parts = raw_line.rstrip("\r\n").split("\t")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": raw_line[:500]})
        rows.append(dict(zip(FIELDS, (clean(part) for part in parts))))

    write_csv(OUTPUT_CSV, rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_supplier_contract_pricing_replay_adapter",
        "expected_rows": len(rows),
        "pricing_method_rows": sum(1 for row in rows if row["pricing_method_text"]),
        "distinct_pricing_methods": len({row["pricing_method_text"] for row in rows if row["pricing_method_text"]}),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
