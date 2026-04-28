#!/usr/bin/env python3
"""Build replay payload for legacy tax deduction facts from restored LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_tax_deduction_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_tax_deduction_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
SEP = "\x1f"

FIELDS = [
    "legacy_line_id",
    "legacy_header_id",
    "legacy_pid",
    "source_table",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "partner_credit_code",
    "invoice_no",
    "invoice_code",
    "invoice_date",
    "invoice_amount_untaxed",
    "invoice_tax_amount",
    "invoice_amount_total",
    "deduction_amount",
    "deduction_tax_amount",
    "deduction_surcharge_amount",
    "deduction_confirm_date",
    "note",
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
  ISNULL(cb.Id, ''),
  ISNULL(cb.ZBID, ''),
  ISNULL(CAST(cb.pid AS varchar(50)), ''),
  'C_JXXP_DKDJ_CB',
  ISNULL(h.DJBH, ''),
  ISNULL(CONVERT(varchar(10), h.DJRQ, 23), ''),
  ISNULL(h.DJZT, ''),
  CAST(ISNULL(h.DEL, 0) AS varchar(20)),
  ISNULL(h.XMID, ''),
  REPLACE(REPLACE(ISNULL(h.XMMC, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(cb.KPDWID, ''),
  REPLACE(REPLACE(ISNULL(cb.KPDW, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(cb.KPDWXYDM, ''),
  ISNULL(cb.FPHM, ''),
  ISNULL(cb.FPDM, ''),
  ISNULL(CONVERT(varchar(10), cb.KPRQ, 23), ''),
  CAST(ISNULL(cb.JE_NO, 0) AS varchar(50)),
  CAST(ISNULL(cb.SE, 0) AS varchar(50)),
  CAST(ISNULL(cb.JE, 0) AS varchar(50)),
  CAST(ISNULL(cb.DKJE, 0) AS varchar(50)),
  CAST(ISNULL(cb.DKSE, 0) AS varchar(50)),
  CAST(ISNULL(cb.D_SCBSJS_DKFJS, 0) AS varchar(50)),
  ISNULL(CONVERT(varchar(10), cb.RZDKRQ, 23), ''),
  REPLACE(REPLACE(ISNULL(cb.BZ, ''), CHAR(31), ' '), CHAR(9), ' '),
  'legacy_tax_deduction_v1'
)
FROM dbo.C_JXXP_DKDJ_CB cb
JOIN dbo.C_JXXP_DKDJ_New h ON h.Id = cb.ZBID
WHERE ISNULL(h.DEL, 0) = 0
ORDER BY h.DJRQ, h.DJBH, cb.Id;
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
    payload = {
        "status": "PASS",
        "mode": "fresh_db_legacy_tax_deduction_replay_adapter",
        "expected_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
