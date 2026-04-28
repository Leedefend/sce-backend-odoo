#!/usr/bin/env python3
"""Build replay payload for actual-outflow child line facts from restored LegacyDb."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_line_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_line_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")


FIELDS = [
    "external_id",
    "parent_actual_outflow_id",
    "legacy_line_id",
    "legacy_parent_id",
    "legacy_supplier_contract_id",
    "source_document_no",
    "source_line_type",
    "source_counterparty_text",
    "source_contract_no",
    "amount",
    "paid_before_amount",
    "remaining_amount",
    "current_pay_amount",
    "estimated_amount",
    "actual_pay_amount",
    "is_estimated",
    "note",
]


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_sql() -> str:
    clean = "REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"
    sql = f"""
SET NOCOUNT ON;
SELECT
  {clean.format(field="'legacy_actual_outflow_line_sc_' + REPLACE(REPLACE(Id, '-', '_'), ' ', '_')")} AS external_id,
  {clean.format(field="T_FK_Supplier_ID")} AS parent_actual_outflow_id,
  {clean.format(field="'actual_outflow_line:' + Id")} AS legacy_line_id,
  {clean.format(field="T_FK_Supplier_ID")} AS legacy_parent_id,
  {clean.format(field="GLYWID")} AS legacy_supplier_contract_id,
  {clean.format(field="DJBH")} AS source_document_no,
  {clean.format(field="LX")} AS source_line_type,
  {clean.format(field="SupplierId")} AS source_counterparty_text,
  {clean.format(field="DJBH")} AS source_contract_no,
  CONVERT(varchar(80), COALESCE(NULLIF(SJZFJE, 0), NULLIF(CCZFJE, 0), NULLIF(ZJE, 0), 0)) AS amount,
  CONVERT(varchar(80), COALESCE(YGLZF, 0)) AS paid_before_amount,
  CONVERT(varchar(80), COALESCE(SY, 0)) AS remaining_amount,
  CONVERT(varchar(80), COALESCE(CCZFJE, 0)) AS current_pay_amount,
  CONVERT(varchar(80), COALESCE(YJJE, 0)) AS estimated_amount,
  CONVERT(varchar(80), COALESCE(SJZFJE, 0)) AS actual_pay_amount,
  {clean.format(field="IsYJ")} AS is_estimated,
  {clean.format(field="'[migration:actual_outflow_line] legacy_actual_outflow_line_id=' + Id + '; legacy_actual_outflow_id=' + COALESCE(T_FK_Supplier_ID, '') + '; source_table=T_FK_Supplier_CB; line_fact=true; not_ledger=true; not_settlement=true'")} AS note
FROM dbo.T_FK_Supplier_CB
WHERE NULLIF(LTRIM(RTRIM(Id)), '') IS NOT NULL
ORDER BY T_FK_Supplier_ID, pid, Id;
"""
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


def main() -> int:
    raw = run_sql()
    rows: list[list[str]] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
        rows.append(parts)

    csv_lines = ["\ufeff" + ",".join(FIELDS)]
    for parts in rows:
        escaped = []
        for value in parts:
            text = value.replace('"', '""')
            escaped.append(f'"{text}"')
        csv_lines.append(",".join(escaped))
    write_text(OUTPUT_CSV, "\n".join(csv_lines) + "\n")

    parent_count = len({row[1] for row in rows if row[1]})
    payload = {
        "status": "PASS",
        "mode": "fresh_db_actual_outflow_line_replay_adapter",
        "source_table": "T_FK_Supplier_CB",
        "expected_rows": len(rows),
        "replay_payload_rows": len(rows),
        "distinct_parent_actual_outflow_ids": parent_count,
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_ACTUAL_OUTFLOW_LINE_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
