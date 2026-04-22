#!/usr/bin/env python3
"""Screen legacy outflow request line facts before carrier selection."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_outflow_request_line_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_outflow_request_line_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "legacy_outflow_request_line_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_outflow_request_line_screen_v1.md")
EXPECTED_RAW_ROWS = 17413

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZFSQID) AS ZFSQID,
  CONVERT(nvarchar(max), SupplierId) AS SupplierId,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), YGLZF) AS YGLZF,
  CONVERT(nvarchar(max), SY) AS SY,
  CONVERT(nvarchar(max), CCZFJE) AS CCZFJE,
  CONVERT(nvarchar(max), LX) AS LX,
  CONVERT(nvarchar(max), GLYWID) AS GLYWID,
  CONVERT(nvarchar(max), D_SCBSJS_DWMC) AS D_SCBSJS_DWMC,
  CONVERT(nvarchar(max), D_SCBSJS_HTZBH) AS D_SCBSJS_HTZBH,
  CONVERT(nvarchar(max), FPBHSJE) AS FPBHSJE
FROM dbo.C_ZFSQGL_CB
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZFSQID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SupplierId, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(YGLZF, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SY, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CCZFJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(LX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(GLYWID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(D_SCBSJS_DWMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(D_SCBSJS_HTZBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPBHSJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id",
    "ZFSQID",
    "SupplierId",
    "DJBH",
    "ZJE",
    "YGLZF",
    "SY",
    "CCZFJE",
    "LX",
    "GLYWID",
    "D_SCBSJS_DWMC",
    "D_SCBSJS_HTZBH",
    "FPBHSJE",
]


class OutflowRequestLineScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise OutflowRequestLineScreenError(message)


def run_sql() -> str:
    cmd = [
        "docker",
        "exec",
        "-i",
        "legacy-sqlserver",
        "bash",
        "-lc",
        "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -W -s '|'",
    ]
    completed = subprocess.run(cmd, input=SQL, text=True, capture_output=True, check=False)
    require(completed.returncode == 0, completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout


def parse_sql_rows(output: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in output.splitlines():
        text = line.strip()
        if not text or text == "rowdata" or set(text) <= {"-"}:
            continue
        parts = [part.strip() for part in text.split("|")]
        if len(parts) != len(SQL_COLUMNS):
            continue
        rows.append(dict(zip(SQL_COLUMNS, parts)))
    require(len(rows) == EXPECTED_RAW_ROWS, f"raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return rows


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_outflow_request_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/outflow_request_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_outflow_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "outflow request anchor map is empty")
    return result


def load_supplier_contract_map(asset_root: Path) -> dict[str, str]:
    path = asset_root / "manifest/supplier_contract_external_id_manifest_v1.json"
    if not path.exists():
        return {}
    manifest = load_json(path)
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_supplier_contract_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("ZJE", "CCZFJE", "FPBHSJE"):
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_outflow_line_id",
        "legacy_outflow_id",
        "outflow_request_external_id",
        "legacy_supplier_contract_id",
        "supplier_contract_external_id",
        "amount",
        "amount_source",
        "line_type",
        "route",
        "blockers",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def screen(asset_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    rows = parse_sql_rows(run_sql())
    outflow_by_legacy = load_outflow_request_map(asset_root)
    supplier_contract_by_legacy = load_supplier_contract_map(asset_root)
    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    line_type_counts: Counter[str] = Counter()
    supplier_contract_anchor_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        legacy_line_id = clean(row.get("Id"))
        legacy_outflow_id = clean(row.get("ZFSQID"))
        outflow_external_id = outflow_by_legacy.get(legacy_outflow_id, "")
        legacy_supplier_contract_id = clean(row.get("GLYWID"))
        supplier_contract_external_id = supplier_contract_by_legacy.get(legacy_supplier_contract_id, "")
        amount_source, amount = best_amount(row)
        line_type = clean(row.get("LX")) or "blank"
        line_type_counts[line_type] += 1
        blockers: list[str] = []
        if not legacy_line_id:
            blockers.append("missing_legacy_outflow_line_id")
        if not legacy_outflow_id:
            blockers.append("missing_parent_outflow_id")
        elif not outflow_external_id:
            blockers.append("outflow_request_anchor_missing")
        if amount <= 0:
            blockers.append("amount_not_positive")

        if supplier_contract_external_id:
            supplier_contract_anchor_counts["supplier_contract_anchor_resolved"] += 1
        elif legacy_supplier_contract_id:
            supplier_contract_anchor_counts["supplier_contract_anchor_unresolved"] += 1
        else:
            supplier_contract_anchor_counts["supplier_contract_anchor_empty"] += 1

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            if "outflow_request_anchor_missing" in blockers or "missing_parent_outflow_id" in blockers:
                route = "block_outflow_request_anchor_missing"
            elif "amount_not_positive" in blockers:
                route = "block_amount_not_positive"
            else:
                route = "manual_review_hold"
            route_counts[route] += 1
        else:
            route = "loadable_candidate_line_fact"
            route_counts[route] += 1
            amount_source_counts[amount_source] += 1

        output_rows.append(
            {
                "legacy_outflow_line_id": legacy_line_id,
                "legacy_outflow_id": legacy_outflow_id,
                "outflow_request_external_id": outflow_external_id,
                "legacy_supplier_contract_id": legacy_supplier_contract_id,
                "supplier_contract_external_id": supplier_contract_external_id,
                "amount": str(amount),
                "amount_source": amount_source,
                "line_type": line_type,
                "route": route,
                "blockers": ",".join(blockers),
            }
        )

    loadable = route_counts["loadable_candidate_line_fact"]
    payload = {
        "status": "PASS",
        "source_table": "C_ZFSQGL_CB",
        "lane": "outflow_request_line",
        "target_model_candidate": "carrier_not_selected",
        "raw_rows": len(rows),
        "loadable_candidate_rows": loadable,
        "blocked_rows": len(rows) - loadable,
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "amount_source_counts": dict(sorted(amount_source_counts.items())),
        "line_type_counts": dict(sorted(line_type_counts.items())),
        "supplier_contract_anchor_counts": dict(sorted(supplier_contract_anchor_counts.items())),
        "required_facts": ["outflow_request_anchor", "amount_positive", "stable line id"],
        "optional_facts": ["supplier_contract_anchor", "line_type", "counterparty text"],
        "decision": "outflow_request line_fact candidates require a carrier screen before XML generation",
        "next_step": "screen target carrier for outflow_request_line facts; do not weaken parent anchor requirement",
    }
    return payload, output_rows


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    amount_rows = "\n".join(f"| {source} | {count} |" for source, count in payload["amount_source_counts"].items())
    supplier_rows = "\n".join(
        f"| {route} | {count} |" for route, count in payload["supplier_contract_anchor_counts"].items()
    )
    return f"""# Legacy Outflow Request Line Screen v1

Status: `{payload["status"]}`

This is a read-only old-database screen for outflow request `line_fact` rows
before target carrier selection.

## Required Facts

- stable line id
- outflow_request_anchor
- amount_positive

Supplier contract anchor is optional at this stage because many source rows
only carry parent request and amount facts.

## Result

- source table: `{payload["source_table"]}`
- raw rows: `{payload["raw_rows"]}`
- loadable candidates: `{payload["loadable_candidate_rows"]}`
- blocked/discarded rows: `{payload["blocked_rows"]}`
- target model candidate: `{payload["target_model_candidate"]}`
- DB writes: `0`
- Odoo shell: `false`

## Routes

| Route | Rows |
|---|---:|
{route_rows}

## Blockers

| Blocker | Rows |
|---|---:|
{blocker_rows}

## Amount Sources

| Source | Rows |
|---|---:|
{amount_rows}

## Supplier Contract Anchor

| Status | Rows |
|---|---:|
{supplier_rows}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def run(asset_root: Path, check: bool) -> dict[str, Any]:
    payload, rows = screen(asset_root)
    write_json(OUTPUT_JSON, payload)
    write_csv(OUTPUT_CSV, rows)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    if check:
        require(payload["raw_rows"] == EXPECTED_RAW_ROWS, "raw row count mismatch")
        require(payload["loadable_candidate_rows"] > 0, "no outflow request line candidates")
        require(OUTPUT_JSON.exists(), f"missing output: {OUTPUT_JSON}")
        require(OUTPUT_CSV.exists(), f"missing output: {OUTPUT_CSV}")
        require(OUTPUT_MD.exists(), f"missing output: {OUTPUT_MD}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy outflow request line facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = run(Path(args.asset_root), args.check)
    except (OutflowRequestLineScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("OUTFLOW_REQUEST_LINE_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "OUTFLOW_REQUEST_LINE_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "raw_rows": payload["raw_rows"],
                "loadable_candidate_rows": payload["loadable_candidate_rows"],
                "blocked_rows": payload["blocked_rows"],
                "db_writes": 0,
                "odoo_shell": False,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
