#!/usr/bin/env python3
"""Probe legacy MSSQL rows for visible balance cleanup observations."""

from __future__ import annotations

import csv
import json
import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(os.getenv("ROOT_DIR", Path.cwd()))
ARTIFACT_ROOT = Path(
    os.getenv(
        "MIGRATION_ARTIFACT_ROOT",
        str(REPO_ROOT / "artifacts/migration/business_fact_data_cleanup"),
    )
)
OUTPUT_JSON = ARTIFACT_ROOT / "business_fact_visible_balance_legacy_source_probe_result_v1.json"
OUTPUT_CSV = ARTIFACT_ROOT / "business_fact_visible_balance_legacy_source_probe_rows_v1.csv"
OUTPUT_REPORT = ARTIFACT_ROOT / "business_fact_visible_balance_legacy_source_probe_report_v1.md"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD", "LegacyRestore!2026")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def money_text(value: str) -> str:
    return clean(value).lstrip(".") if clean(value).startswith(".") else clean(value)


def cleanup_rows() -> list[dict[str, object]]:
    explicit = os.getenv("BUSINESS_FACT_CLEANUP_RESULT_JSON")
    path = Path(explicit) if explicit else ARTIFACT_ROOT / "business_fact_visible_balance_cleanup_result_v1.json"
    if not path or not path.exists():
        raise RuntimeError(
            {
                "missing_cleanup_result": str(path),
                "action": "run BUSINESS_FACT_REPLAY_MODE=cleanup with the same MIGRATION_ARTIFACT_ROOT, or set BUSINESS_FACT_CLEANUP_RESULT_JSON",
            }
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    return list(payload.get("rows") or [])


def sql_literal(value: object) -> str:
    return "'" + clean(value).replace("'", "''") + "'"


def target_values(rows: list[dict[str, object]]) -> str:
    values = []
    for row in rows:
        legacy_contract_id = clean(row.get("legacy_contract_id"))
        document_no = clean(row.get("legacy_document_no"))
        if not legacy_contract_id and not document_no:
            continue
        values.append(f"({sql_literal(legacy_contract_id)}, {sql_literal(document_no)})")
    if not values:
        raise RuntimeError("cleanup rows do not include legacy contract identities")
    return ",\n    ".join(values)


def run_sql(query: str) -> list[list[str]]:
    command = [
        "docker",
        "exec",
        "-i",
        SQL_CONTAINER,
        "bash",
        "-lc",
        (
            f"{SQLCMD} -S localhost -U sa -P {sql_literal(SQL_PASSWORD)} -C "
            f"-d {sql_literal(SQL_DATABASE)} -h -1 -s '|'"
        ),
    ]
    completed = subprocess.run(command, input=query, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            {
                "legacy_mssql_probe_failed": completed.returncode,
                "stdout": completed.stdout[-2000:],
                "stderr": completed.stderr[-2000:],
            }
        )
    rows = []
    for line in completed.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("(") or line.startswith("-"):
            continue
        rows.append([item.strip() for item in line.split("|")])
    return rows


def query_contract_rows(values_sql: str) -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
WITH target(legacy_contract_id, legacy_document_no) AS (
  SELECT * FROM (VALUES
    {values_sql}
  ) v(legacy_contract_id, legacy_document_no)
)
SELECT
  t.legacy_contract_id,
  t.legacy_document_no,
  ISNULL(c.Id, '') AS source_id,
  ISNULL(c.DJBH, '') AS source_document_no,
  ISNULL(c.HTBH, '') AS source_contract_no,
  ISNULL(c.HTBT, '') AS source_title,
  ISNULL(c.FBF, '') AS source_owner,
  ISNULL(c.CBF, '') AS source_contractor,
  ISNULL(CONVERT(varchar(40), CAST(c.GCYSZJ AS decimal(18,2))), '') AS source_contract_amount,
  ISNULL(CONVERT(varchar(40), CAST(c.f_HTJK AS decimal(18,2))), '') AS source_contract_receipt_amount,
  ISNULL(c.GCLJKPJE, '') AS source_visible_invoice_text,
  ISNULL(c.GCLJYSK_1, '') AS source_visible_receipt_text_1,
  ISNULL(c.GCLJYSK_2, '') AS source_visible_receipt_text_2,
  ISNULL(c.GCQK, '') AS source_visible_unreceived_text,
  ISNULL(c.DJZT, '') AS source_document_state,
  ISNULL(CONVERT(varchar(20), c.DEL), '') AS source_deleted_flag,
  ISNULL(c.SCRID, '') AS source_deleted_user,
  ISNULL(CONVERT(varchar(23), c.SCRQ, 121), '') AS source_deleted_at
FROM target t
LEFT JOIN dbo.T_ProjectContract_Out c
  ON c.Id = t.legacy_contract_id OR c.DJBH = t.legacy_document_no
ORDER BY t.legacy_document_no;
"""
    fields = [
        "legacy_contract_id",
        "legacy_document_no",
        "source_id",
        "source_document_no",
        "source_contract_no",
        "source_title",
        "source_owner",
        "source_contractor",
        "source_contract_amount",
        "source_contract_receipt_amount",
        "source_visible_invoice_text",
        "source_visible_receipt_text_1",
        "source_visible_receipt_text_2",
        "source_visible_unreceived_text",
        "source_document_state",
        "source_deleted_flag",
        "source_deleted_user",
        "source_deleted_at",
    ]
    return [dict(zip(fields, row)) for row in run_sql(sql)]


def query_aggregates(values_sql: str, source: str) -> dict[str, dict[str, str]]:
    if source == "receipt":
        sql = f"""
SET NOCOUNT ON;
WITH target(legacy_contract_id, legacy_document_no) AS (
  SELECT * FROM (VALUES
    {values_sql}
  ) v(legacy_contract_id, legacy_document_no)
)
SELECT
  t.legacy_contract_id,
  COUNT(r.Id) AS linked_rows,
  ISNULL(CONVERT(varchar(40), CAST(COALESCE(SUM(CASE WHEN ISNULL(r.DEL,0)=0 THEN r.f_JE ELSE 0 END),0) AS decimal(18,2))), '0.00') AS active_amount,
  ISNULL(CONVERT(varchar(40), CAST(COALESCE(SUM(r.f_JE),0) AS decimal(18,2))), '0.00') AS raw_amount
FROM target t
LEFT JOIN dbo.C_JFHKLR r
  ON r.SGHTID = t.legacy_contract_id OR r.GLHTID = t.legacy_contract_id OR r.HTID = t.legacy_contract_id
GROUP BY t.legacy_contract_id
ORDER BY t.legacy_contract_id;
"""
    else:
        sql = f"""
SET NOCOUNT ON;
WITH target(legacy_contract_id, legacy_document_no) AS (
  SELECT * FROM (VALUES
    {values_sql}
  ) v(legacy_contract_id, legacy_document_no)
)
SELECT
  t.legacy_contract_id,
  COUNT(h.Id) AS linked_rows,
  ISNULL(CONVERT(varchar(40), CAST(COALESCE(SUM(CASE WHEN ISNULL(h.DEL,0)=0 THEN h.KPZJE ELSE 0 END),0) AS decimal(18,2))), '0.00') AS active_amount,
  ISNULL(CONVERT(varchar(40), CAST(COALESCE(SUM(h.KPZJE),0) AS decimal(18,2))), '0.00') AS raw_amount
FROM target t
LEFT JOIN dbo.C_JXXP_XXKPDJ h
  ON h.D_JCLY_GLHTID = t.legacy_contract_id
  OR h.D_JCLY_GLHTID = t.legacy_document_no
  OR h.DJBH = t.legacy_document_no
  OR h.OTHER_SYSTEM_ID = t.legacy_contract_id
GROUP BY t.legacy_contract_id
ORDER BY t.legacy_contract_id;
"""
    fields = ["legacy_contract_id", f"{source}_linked_rows", f"{source}_active_amount", f"{source}_raw_amount"]
    return {row[0]: dict(zip(fields, row)) for row in run_sql(sql)}


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_contract_id",
        "legacy_document_no",
        "source_document_no",
        "source_contract_no",
        "source_title",
        "source_contract_amount",
        "source_contract_receipt_amount",
        "source_visible_invoice_text",
        "source_visible_receipt_text_1",
        "source_visible_receipt_text_2",
        "source_visible_unreceived_text",
        "receipt_linked_rows",
        "receipt_active_amount",
        "invoice_linked_rows",
        "invoice_active_amount",
        "source_fact_decision",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(payload: dict[str, object]) -> None:
    text = f"""# Business Fact Visible Balance Legacy Source Probe v1

Status: {payload["status"]}

Task: `ITER-2026-05-07-BUSINESS-FACT-DATA-CLEANUP`

## Summary

```json
{json.dumps(payload["summary"], ensure_ascii=False, indent=2)}
```

## Rows

```json
{json.dumps(payload["rows"], ensure_ascii=False, indent=2)}
```

## Decision

`{payload["decision"]}`
"""
    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(text, encoding="utf-8")


rows = cleanup_rows()
values_sql = target_values(rows)
contract_rows = query_contract_rows(values_sql)
receipt_by_contract = query_aggregates(values_sql, "receipt")
invoice_by_contract = query_aggregates(values_sql, "invoice")

merged: list[dict[str, object]] = []
for row in contract_rows:
    legacy_contract_id = clean(row.get("legacy_contract_id"))
    merged_row = {
        **row,
        **receipt_by_contract.get(legacy_contract_id, {}),
        **invoice_by_contract.get(legacy_contract_id, {}),
    }
    receipt_rows = int(clean(merged_row.get("receipt_linked_rows")) or 0)
    invoice_rows = int(clean(merged_row.get("invoice_linked_rows")) or 0)
    source_visible_text = any(
        clean(merged_row.get(field))
        for field in (
            "source_contract_receipt_amount",
            "source_visible_invoice_text",
            "source_visible_receipt_text_1",
            "source_visible_receipt_text_2",
            "source_visible_unreceived_text",
        )
    )
    if receipt_rows or invoice_rows:
        decision = "legacy_transaction_detail_exists_review_for_replay_lane"
    elif source_visible_text:
        decision = "legacy_contract_surface_text_only_no_linked_transaction_detail"
    else:
        decision = "legacy_contract_header_only_no_linked_transaction_detail"
    merged_row["source_fact_decision"] = decision
    for field in ("receipt_active_amount", "receipt_raw_amount", "invoice_active_amount", "invoice_raw_amount"):
        merged_row[field] = money_text(clean(merged_row.get(field)))
    merged.append(merged_row)

summary = {
    "legacy_mssql_container": SQL_CONTAINER,
    "legacy_mssql_database": SQL_DATABASE,
    "probed_rows": len(merged),
    "source_contract_rows_found": sum(1 for row in merged if clean(row.get("source_id"))),
    "receipt_linked_rows": sum(int(clean(row.get("receipt_linked_rows")) or 0) for row in merged),
    "invoice_linked_rows": sum(int(clean(row.get("invoice_linked_rows")) or 0) for row in merged),
    "decisions": {},
}
for row in merged:
    decision = clean(row["source_fact_decision"])
    summary["decisions"][decision] = int(summary["decisions"].get(decision, 0)) + 1

errors = []
if summary["source_contract_rows_found"] != len(merged):
    errors.append(
        {
            "error": "missing_legacy_contract_source_rows",
            "actual": summary["source_contract_rows_found"],
            "expected": len(merged),
        }
    )

status = "PASS" if not errors else "FAIL"
payload = {
    "status": status,
    "mode": "business_fact_visible_balance_legacy_source_probe",
    "summary": summary,
    "rows": merged,
    "errors": errors,
    "decision": "legacy_source_probe_confirms_no_linked_transaction_detail_for_visible_balance_observations"
    if status == "PASS"
    else "STOP_REVIEW_REQUIRED",
}
OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
write_csv(OUTPUT_CSV, merged)
write_report(payload)
print(
    "BUSINESS_FACT_VISIBLE_BALANCE_LEGACY_SOURCE_PROBE="
    + json.dumps(
        {
            "status": status,
            "probed_rows": summary["probed_rows"],
            "source_contract_rows_found": summary["source_contract_rows_found"],
            "receipt_linked_rows": summary["receipt_linked_rows"],
            "invoice_linked_rows": summary["invoice_linked_rows"],
            "decisions": summary["decisions"],
        },
        ensure_ascii=False,
        sort_keys=True,
    )
)
