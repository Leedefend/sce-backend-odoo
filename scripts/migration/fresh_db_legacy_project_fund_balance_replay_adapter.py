#!/usr/bin/env python3
"""Build replay payload for legacy project fund balance facts."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_project_fund_balance_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_project_fund_balance_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
SEP = "\x1f"

FIELDS = [
    "legacy_project_id",
    "project_name",
    "project_self_funding_amount",
    "actual_receipt_amount",
    "receipt_amount",
    "payment_amount",
    "external_fund_amount",
    "in_transit_amount",
    "actual_available_balance",
    "book_balance",
    "import_batch",
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        "-h",
        "-1",
        "-Q",
        sql,
    ]
    return subprocess.check_output(cmd, text=True)


def main() -> int:
    sql = r"""
SET NOCOUNT ON;
SELECT CONCAT_WS(CHAR(31),
  ISNULL(v.ID, ''),
  REPLACE(REPLACE(ISNULL(p.XMMC, ''), CHAR(31), ' '), CHAR(9), ' '),
  CAST(ISNULL(v.XMZCZ, 0) AS varchar(50)),
  CAST(ISNULL(v.LJSK_SJ, 0) AS varchar(50)),
  CAST(ISNULL(v.LJSK, 0) AS varchar(50)),
  CAST(ISNULL(v.LJFK, 0) AS varchar(50)),
  CAST(ISNULL(v.WLZJ, 0) AS varchar(50)),
  CAST(ISNULL(v.ZTZJ, 0) AS varchar(50)),
  CAST(ISNULL(v.SJKYYE, 0) AS varchar(50)),
  CAST(ISNULL(v.ZMYE, 0) AS varchar(50)),
  'legacy_project_fund_balance_v1'
)
FROM dbo.View_Select_XMCKXX_BS v
LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID = v.ID;
"""
    rows: list[dict[str, str]] = []
    for raw_line in run_sql(sql).splitlines():
        line = raw_line.rstrip("\r\n")
        if not line or line.startswith("("):
            continue
        parts = line.split(SEP)
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
        rows.append(dict(zip(FIELDS, (clean(part) for part in parts))))

    write_csv(OUTPUT_CSV, rows)
    amount = sum(float(row["actual_available_balance"] or 0.0) for row in rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_project_fund_balance_replay_adapter",
        "expected_rows": len(rows),
        "actual_available_balance": round(amount, 2),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
