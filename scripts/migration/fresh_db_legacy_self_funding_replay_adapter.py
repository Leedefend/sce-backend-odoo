#!/usr/bin/env python3
"""Build replay payload for legacy self-funding facts from restored LegacyDb."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_legacy_self_funding_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_legacy_self_funding_replay_adapter_result_v1.json"
SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_PASSWORD", "LegacyRestore!2026")
SEP = "\x1f"

FIELDS = [
    "source_table",
    "legacy_record_id",
    "legacy_header_id",
    "legacy_pid",
    "line_type",
    "document_no",
    "document_date",
    "document_state",
    "deleted_flag",
    "project_legacy_id",
    "project_name",
    "partner_legacy_id",
    "partner_name",
    "income_category",
    "receipt_type",
    "legacy_category",
    "self_funding_amount",
    "refund_amount",
    "unreturned_amount",
    "payment_method",
    "account_name",
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
  'C_JFHKLR',
  ISNULL(Id, ''),
  '',
  ISNULL(CAST(PID AS varchar(50)), ''),
  'income',
  ISNULL(DJBH, ''),
  ISNULL(CONVERT(varchar(10), f_RQ, 23), ''),
  ISNULL(DJZT, ''),
  CAST(ISNULL(DEL, 0) AS varchar(20)),
  ISNULL(XMID, ''),
  REPLACE(REPLACE(ISNULL(XMMC, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(WLDWID, ''),
  REPLACE(REPLACE(ISNULL(WLDWMC, ''), CHAR(31), ' '), CHAR(9), ' '),
  REPLACE(REPLACE(ISNULL(f_SRLBName, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(type, ''),
  ISNULL(LX, ''),
  CAST(ISNULL(f_JE, 0) AS varchar(50)),
  '0',
  CAST(ISNULL(f_JE, 0) AS varchar(50)),
  ISNULL(FKFSMC, ''),
  ISNULL(SKZH, ''),
  REPLACE(REPLACE(ISNULL(f_BZ, ''), CHAR(31), ' '), CHAR(9), ' '),
  'legacy_self_funding_v1'
)
FROM dbo.C_JFHKLR
WHERE ISNULL(DJZT,'0')='2'
  AND ISNULL(DEL,0)=0
  AND ISNULL(LX,'')='自筹垫付'
  AND ISNULL(type,'正常类型收款')='其他类型收款'
UNION ALL
SELECT CONCAT_WS(CHAR(31),
  'C_JFHKLR_TH_ZCDF_CB',
  ISNULL(cb.Id, ''),
  ISNULL(zb.Id, ''),
  ISNULL(CAST(cb.pid AS varchar(50)), ''),
  'refund',
  ISNULL(zb.DJBH, ''),
  ISNULL(CONVERT(varchar(10), zb.DJRQ, 23), ''),
  ISNULL(zb.DJZT, ''),
  CAST(ISNULL(zb.DEL, 0) AS varchar(20)),
  ISNULL(zb.XMID, ''),
  REPLACE(REPLACE(ISNULL(zb.XMMC, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(cb.JNDWID, ''),
  REPLACE(REPLACE(ISNULL(cb.JNDW, ''), CHAR(31), ' '), CHAR(9), ' '),
  ISNULL(cb.ZJLB, ''),
  ISNULL(cb.JNFS, ''),
  '自筹退回',
  '0',
  CAST(ISNULL(cb.BCTK, 0) AS varchar(50)),
  CAST(0 - ISNULL(cb.BCTK, 0) AS varchar(50)),
  ISNULL(cb.JNFS, ''),
  ISNULL(cb.THZH, ''),
  REPLACE(REPLACE(ISNULL(cb.BZ, ''), CHAR(31), ' '), CHAR(9), ' '),
  'legacy_self_funding_v1'
)
FROM dbo.C_JFHKLR_TH_ZCDF zb
JOIN dbo.C_JFHKLR_TH_ZCDF_CB cb ON zb.Id=cb.ZBID
WHERE ISNULL(zb.DJZT,'0')='2'
  AND ISNULL(zb.DEL,0)=0;
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
        "mode": "fresh_db_legacy_self_funding_replay_adapter",
        "expected_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
