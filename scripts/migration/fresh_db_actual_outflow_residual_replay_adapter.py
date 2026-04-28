#!/usr/bin/env python3
"""Build residual actual-outflow parent payloads from restored LegacyDb.

This lane preserves parent facts needed by ``T_FK_Supplier_CB`` child lines when
the original strict core lane excluded the parent because of deletion/amount or
other historical-rule drift.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_CSV = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_residual_replay_payload_v1.csv"
OUTPUT_JSON = REPO_ROOT / "artifacts/migration/fresh_db_actual_outflow_residual_replay_adapter_result_v1.json"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")


FIELDS = [
    "external_id",
    "type",
    "project_ref",
    "partner_ref",
    "legacy_actual_outflow_id",
    "legacy_project_id",
    "legacy_project_name",
    "legacy_project_code",
    "legacy_partner_id",
    "legacy_partner_name",
    "legacy_request_id",
    "amount",
    "date_request",
    "document_no",
    "deleted_flag",
    "document_state",
    "line_count",
    "note",
]


def clean_sql(field: str) -> str:
    return f"REPLACE(REPLACE(REPLACE(COALESCE(CONVERT(varchar(max), {field}), ''), CHAR(9), ' '), CHAR(10), ' '), CHAR(13), ' ')"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_sql() -> str:
    sql = f"""
SET NOCOUNT ON;
WITH line_parent AS (
  SELECT T_FK_Supplier_ID, COUNT(*) AS line_count
  FROM dbo.T_FK_Supplier_CB
  WHERE NULLIF(LTRIM(RTRIM(T_FK_Supplier_ID)), '') IS NOT NULL
  GROUP BY T_FK_Supplier_ID
)
SELECT
  {clean_sql("'legacy_actual_outflow_residual_sc_' + REPLACE(REPLACE(h.Id, '-', '_'), ' ', '_')")} AS external_id,
  'pay' AS type,
  {clean_sql("'legacy_project_sc_' + COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))")} AS project_ref,
  {clean_sql("'legacy_partner_sc_' + REPLACE(REPLACE(COALESCE(h.f_SupplierID, ''), '-', '_'), ' ', '_')")} AS partner_ref,
  {clean_sql("h.Id")} AS legacy_actual_outflow_id,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))")} AS legacy_project_id,
  {clean_sql("COALESCE(p.XMMC, h.XMMC, h.f_LYXM, h.TSXMMC)")} AS legacy_project_name,
  {clean_sql("p.PROJECT_CODE")} AS legacy_project_code,
  {clean_sql("h.f_SupplierID")} AS legacy_partner_id,
  {clean_sql("h.f_SupplierName")} AS legacy_partner_name,
  {clean_sql("h.f_ZFSQGLId")} AS legacy_request_id,
  CONVERT(varchar(80), COALESCE(h.f_FKJE, 0)) AS amount,
  COALESCE(CONVERT(varchar(10), h.f_FKRQ, 23), '') AS date_request,
  {clean_sql("COALESCE(NULLIF(LTRIM(RTRIM(h.DJBH)), ''), h.ZFSQDH)")} AS document_no,
  {clean_sql("h.DEL")} AS deleted_flag,
  {clean_sql("h.DJZT")} AS document_state,
  CONVERT(varchar(20), lp.line_count) AS line_count,
  {clean_sql("'[migration:actual_outflow_core] [migration:actual_outflow_residual] legacy_actual_outflow_id=' + h.Id + '; legacy_project_id=' + COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''), '') + '; legacy_partner_id=' + COALESCE(h.f_SupplierID, '') + '; legacy_request_id=' + COALESCE(h.f_ZFSQGLId, '') + '; document_no=' + COALESCE(NULLIF(LTRIM(RTRIM(h.DJBH)), ''), h.ZFSQDH, '') + '; deleted_flag=' + COALESCE(CONVERT(varchar(max), h.DEL), '') + '; document_state=' + COALESCE(CONVERT(varchar(max), h.DJZT), '') + '; residual_parent_for_actual_outflow_line=true; source_table=T_FK_Supplier; not_ledger=true; not_settlement=true'")} AS note
FROM dbo.T_FK_Supplier h
JOIN line_parent lp ON lp.T_FK_Supplier_ID = h.Id
LEFT JOIN dbo.BASE_SYSTEM_PROJECT p ON p.ID = COALESCE(NULLIF(LTRIM(RTRIM(h.f_XMID)), ''), NULLIF(LTRIM(RTRIM(h.f_LYXMID)), ''), NULLIF(LTRIM(RTRIM(h.TSXMID)), ''))
WHERE NULLIF(LTRIM(RTRIM(h.Id)), '') IS NOT NULL
ORDER BY h.Id;
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
    rows: list[dict[str, str]] = []
    for line in run_sql().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("(") and stripped.endswith("rows affected)"):
            continue
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) != len(FIELDS):
            raise RuntimeError({"unexpected_sqlcmd_row_shape": len(parts), "expected": len(FIELDS), "line": line[:500]})
        rows.append(dict(zip(FIELDS, parts)))

    write_csv(OUTPUT_CSV, rows)
    payload = {
        "status": "PASS",
        "mode": "fresh_db_actual_outflow_residual_replay_adapter",
        "source_table": "T_FK_Supplier",
        "expected_rows": len(rows),
        "replay_payload_rows": len(rows),
        "payload_csv": str(OUTPUT_CSV),
    }
    write_json(OUTPUT_JSON, payload)
    print("FRESH_DB_ACTUAL_OUTFLOW_RESIDUAL_REPLAY_ADAPTER=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
