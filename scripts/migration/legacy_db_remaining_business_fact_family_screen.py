#!/usr/bin/env python3
"""Screen remaining legacy business fact candidates by source family."""

from __future__ import annotations

import json
import os
import re
import subprocess
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


ARTIFACT_ROOT = Path(os.getenv("MIGRATION_ARTIFACT_ROOT", "artifacts/migration/business_fact_upgrade"))
SCAN_JSON = ARTIFACT_ROOT / "legacy_db_full_business_fact_loss_scan_v1.json"
OUTPUT_JSON = ARTIFACT_ROOT / "legacy_db_remaining_business_fact_family_screen_v1.json"
OUTPUT_MD = ARTIFACT_ROOT / "legacy_db_remaining_business_fact_family_screen_v1.md"

SQL_CONTAINER = os.getenv("LEGACY_MSSQL_CONTAINER", "legacy-mssql-restore")
SQL_DATABASE = os.getenv("LEGACY_MSSQL_DATABASE", "LegacyDb")
SQL_PASSWORD = os.getenv("LEGACY_MSSQL_SA_PASSWORD") or os.getenv("LEGACY_MSSQL_PASSWORD") or "LegacyRestore!2026"
SQLCMD = os.getenv("LEGACY_SQLCMD", "/opt/mssql-tools18/bin/sqlcmd")

TARGET_FAMILIES = [
    "bid_tender",
    "material_stock",
    "labor_subcontract",
    "lease_equipment",
    "income_invoice",
    "payment_fund",
    "project_settlement",
    "office_admin",
    "cwgl",
    "t",
    "c",
    "s",
]

NUMERIC_TYPES = {"bigint", "decimal", "float", "int", "money", "numeric", "real", "smallint", "smallmoney", "tinyint"}
DATE_TYPES = {"date", "datetime", "datetime2", "smalldatetime"}
AMOUNT_COL = re.compile(r"(JE|AMOUNT|MONEY|PRICE|ZJE|FKJE|SKJE|YSJE|YFJE|SE|TAX|BALANCE|JHJE|SFJE|ZSJE|YJJE|ZLBZJ|HJ|BZJ)", re.IGNORECASE)
DATE_COL = re.compile(r"(RQ|DATE|SJ|TIME|LRR?Q|CREATE|UPDATE|FKSJ|SPSJ)", re.IGNORECASE)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def bracket_ident(value: str) -> str:
    return "[" + value.replace("]", "]]") + "]"


def run_sql(sql: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        SQL_CONTAINER,
        "bash",
        "-lc",
        f"{SQLCMD} -b -S localhost -U sa -P {shell_quote(SQL_PASSWORD)} -C -d {shell_quote(SQL_DATABASE)} -s '|' -y 0 -Y 0",
    ]
    completed = subprocess.run(cmd, input=sql, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError({"sqlcmd_failed": completed.returncode, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]})
    return completed.stdout


def parse_rows(raw: str, expected: int) -> list[list[str]]:
    rows = []
    for line in raw.splitlines():
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != expected:
            continue
        rows.append(parts)
    return rows


def parse_int(value: str | None) -> int | None:
    if value is None or value == "" or value.upper() == "NULL":
        return None
    return int(value)


def load_scan() -> dict[str, Any]:
    if not SCAN_JSON.exists():
        raise RuntimeError({"missing_full_legacy_loss_scan": str(SCAN_JSON)})
    return json.loads(SCAN_JSON.read_text(encoding="utf-8"))


def column_metadata(schema: str, table: str) -> list[dict[str, str]]:
    sql = f"""
SET NOCOUNT ON;
SELECT COLUMN_NAME, DATA_TYPE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = '{schema.replace("'", "''")}'
  AND TABLE_NAME = '{table.replace("'", "''")}'
ORDER BY ORDINAL_POSITION;
"""
    return [{"name": name, "type": col_type} for name, col_type in parse_rows(run_sql(sql), 2)]


def scalar_metrics(schema: str, table: str, columns: list[dict[str, str]]) -> dict[str, Any]:
    col_names = {col["name"] for col in columns}
    del_expr = "NULL"
    active_expr = "COUNT_BIG(*)"
    if "DEL" in col_names:
        del_expr = "SUM(CASE WHEN COALESCE(CONVERT(varchar(max), [DEL]), '0') NOT IN ('0', '', 'False', 'false') THEN 1 ELSE 0 END)"
        active_expr = "SUM(CASE WHEN COALESCE(CONVERT(varchar(max), [DEL]), '0') IN ('0', '', 'False', 'false') THEN 1 ELSE 0 END)"
    elif "SCRQ" in col_names:
        del_expr = "SUM(CASE WHEN [SCRQ] IS NOT NULL THEN 1 ELSE 0 END)"
        active_expr = "SUM(CASE WHEN [SCRQ] IS NULL THEN 1 ELSE 0 END)"

    amount_cols = [
        col["name"]
        for col in columns
        if col["type"].lower() in NUMERIC_TYPES and AMOUNT_COL.search(col["name"])
    ][:8]
    date_cols = [
        col["name"]
        for col in columns
        if col["type"].lower() in DATE_TYPES and DATE_COL.search(col["name"])
    ][:4]
    select_parts = [
        "COUNT_BIG(*) AS total_rows",
        f"{active_expr} AS active_rows",
        f"{del_expr} AS deleted_rows",
    ]
    for col in amount_cols:
        ident = bracket_ident(col)
        select_parts.append(f"COALESCE(SUM(CONVERT(decimal(38, 6), {ident})), 0) AS {bracket_ident('sum__' + col)}")
    for col in date_cols:
        ident = bracket_ident(col)
        select_parts.append(f"CONVERT(varchar(23), MIN({ident}), 121) AS {bracket_ident('min__' + col)}")
        select_parts.append(f"CONVERT(varchar(23), MAX({ident}), 121) AS {bracket_ident('max__' + col)}")

    sql = f"""
SET NOCOUNT ON;
SELECT {' , '.join(select_parts)}
FROM {bracket_ident(schema)}.{bracket_ident(table)};
"""
    raw_rows = parse_rows(run_sql(sql), len(select_parts))
    values = raw_rows[0] if raw_rows else []
    metrics: dict[str, Any] = {
        "total_rows": parse_int(values[0] if len(values) > 0 else None) or 0,
        "active_rows": parse_int(values[1] if len(values) > 1 else None),
        "deleted_rows": parse_int(values[2] if len(values) > 2 else None),
        "amount_columns": amount_cols,
        "date_columns": date_cols,
        "amount_sums": {},
        "date_ranges": {},
    }
    offset = 3
    for col in amount_cols:
        value = values[offset] if offset < len(values) else "0"
        try:
            metrics["amount_sums"][col] = str(Decimal(value))
        except InvalidOperation:
            metrics["amount_sums"][col] = value
        offset += 1
    for col in date_cols:
        min_value = values[offset] if offset < len(values) else ""
        max_value = values[offset + 1] if offset + 1 < len(values) else ""
        metrics["date_ranges"][col] = {"min": min_value, "max": max_value}
        offset += 2
    return metrics


def top_tables(scan: dict[str, Any]) -> list[dict[str, Any]]:
    tables = [
        row
        for row in scan.get("tables", [])
        if row.get("family") in TARGET_FAMILIES
        and row.get("classification") in {"candidate_effective_business_fact", "candidate_secondary_business_fact", "candidate_needs_manual_screen"}
    ]
    tables.sort(key=lambda row: (TARGET_FAMILIES.index(row["family"]), -int(row.get("business_signal_score") or 0), -int(row.get("row_count") or 0), row["table"]))
    selected: list[dict[str, Any]] = []
    per_family: dict[str, int] = {}
    for row in tables:
        family = row["family"]
        if per_family.get(family, 0) >= int(os.getenv("LEGACY_REMAINING_SCREEN_TOP_PER_FAMILY", "12")):
            continue
        selected.append(row)
        per_family[family] = per_family.get(family, 0) + 1
    return selected


def render_markdown(payload: dict[str, Any]) -> str:
    family_rows = "\n".join(
        "| {family} | {tables} | {rows} | {active_rows} | {amount_columns} | {top_tables} |".format(
            family=row["family"],
            tables=row["tables"],
            rows=row["rows"],
            active_rows=row["active_rows"],
            amount_columns=row["amount_columns"],
            top_tables=", ".join(item["table"] for item in row["top_tables"][:5]),
        )
        for row in payload["summary"]["families"]
    )
    table_rows = "\n".join(
        "| {family} | {table} | {classification} | {total_rows} | {active_rows} | {amount_sums} |".format(
            family=row["family"],
            table=row["table"],
            classification=row["classification"],
            total_rows=row["metrics"]["total_rows"],
            active_rows=row["metrics"]["active_rows"],
            amount_sums=", ".join(f"{key}={value}" for key, value in list(row["metrics"]["amount_sums"].items())[:4]),
        )
        for row in payload["screened_tables"]
    )
    return f"""# Legacy DB Remaining Business Fact Family Screen v1

Status: `{payload["status"]}`

Source: `{payload["source"]}`

## Summary

```json
{json.dumps(payload["summary"], ensure_ascii=False, indent=2)}
```

## Families

| Family | Tables Screened | Rows | Active Rows | Amount Columns | Top Tables |
|---|---:|---:|---:|---:|---|
{family_rows}

## Screened Tables

| Family | Table | Classification | Rows | Active Rows | Amount Sums |
|---|---|---|---:|---:|---|
{table_rows}

## Boundary

- Read-only legacy DB screen
- DB writes: `0`
- This file is evidence for lane selection; it is not a replay payload.
"""


def main() -> int:
    scan = load_scan()
    screened = []
    for row in top_tables(scan):
        columns = column_metadata(row["schema"], row["table"])
        screened.append(
            {
                "family": row["family"],
                "schema": row["schema"],
                "table": row["table"],
                "classification": row["classification"],
                "business_signal_score": row["business_signal_score"],
                "scan_row_count": row["row_count"],
                "signals": row.get("signals") or {},
                "metrics": scalar_metrics(row["schema"], row["table"], columns),
            }
        )

    families: dict[str, dict[str, Any]] = {}
    for row in screened:
        family = families.setdefault(
            row["family"],
            {"family": row["family"], "tables": 0, "rows": 0, "active_rows": 0, "amount_columns": 0, "top_tables": []},
        )
        family["tables"] += 1
        family["rows"] += int(row["metrics"]["total_rows"] or 0)
        family["active_rows"] += int(row["metrics"]["active_rows"] or 0)
        family["amount_columns"] += len(row["metrics"]["amount_columns"])
        family["top_tables"].append(
            {
                "table": row["table"],
                "rows": row["metrics"]["total_rows"],
                "active_rows": row["metrics"]["active_rows"],
                "score": row["business_signal_score"],
            }
        )
    family_rows = sorted(families.values(), key=lambda row: (TARGET_FAMILIES.index(row["family"]), -row["rows"]))
    for row in family_rows:
        row["top_tables"] = sorted(row["top_tables"], key=lambda item: (-int(item["score"]), -int(item["rows"]), item["table"]))

    payload = {
        "status": "PASS",
        "mode": "legacy_db_remaining_business_fact_family_screen",
        "source": f"{SQL_CONTAINER}:{SQL_DATABASE}",
        "db_writes": 0,
        "summary": {
            "screened_tables": len(screened),
            "screened_rows": sum(int(row["metrics"]["total_rows"] or 0) for row in screened),
            "screened_active_rows": sum(int(row["metrics"]["active_rows"] or 0) for row in screened),
            "families": family_rows,
        },
        "screened_tables": screened,
        "decision": "remaining_business_fact_families_screened_for_replay_selection",
    }
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    print(
        "LEGACY_DB_REMAINING_BUSINESS_FACT_FAMILY_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "screened_tables": payload["summary"]["screened_tables"],
                "screened_rows": payload["summary"]["screened_rows"],
                "screened_active_rows": payload["summary"]["screened_active_rows"],
                "top_family": (payload["summary"]["families"] or [{}])[0].get("family"),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
