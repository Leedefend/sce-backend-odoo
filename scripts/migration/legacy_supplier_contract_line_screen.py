#!/usr/bin/env python3
"""Screen supplier contract amount facts for target contract-line assets."""

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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_supplier_contract_line_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_supplier_contract_line_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "legacy_supplier_contract_line_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_supplier_contract_line_screen_v1.md")
EXPECTED_RAW_ROWS = 5535

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), ZJE_NO) AS ZJE_NO,
  CONVERT(nvarchar(max), ZSL) AS ZSL,
  CONVERT(nvarchar(max), DJ) AS DJ,
  CONVERT(nvarchar(max), CLMC) AS CLMC,
  CONVERT(nvarchar(max), DEL) AS DEL,
  CONVERT(nvarchar(max), SCRID) AS SCRID,
  CONVERT(nvarchar(max), SCR) AS SCR,
  CONVERT(nvarchar(max), SCRQ, 120) AS SCRQ
FROM dbo.T_GYSHT_INFO
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE_NO, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZSL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CLMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = ["Id", "ZJE", "ZJE_NO", "ZSL", "DJ", "CLMC", "DEL", "SCRID", "SCR", "SCRQ"]


class SupplierContractLineScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SupplierContractLineScreenError(message)


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


def load_supplier_contract_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/supplier_contract_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_supplier_contract_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(len(result) == 5301, f"supplier contract anchor count drifted: {len(result)} != 5301")
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("ZJE", "ZJE_NO"):
        amount = parse_amount(row.get(field))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_supplier_contract_id",
        "contract_external_id",
        "amount",
        "amount_source",
        "qty_source",
        "price_source",
        "line_name_source",
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
    contract_by_legacy = load_supplier_contract_map(asset_root)
    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    amount_source_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        legacy_id = clean(row.get("Id"))
        contract_external_id = contract_by_legacy.get(legacy_id, "")
        amount_source, amount = best_amount(row)
        blockers: list[str] = []
        if not legacy_id:
            blockers.append("missing_legacy_supplier_contract_id")
        if is_deleted(row):
            blockers.append("discard_deleted")
        if not contract_external_id:
            blockers.append("supplier_contract_anchor_missing")
        if amount <= 0:
            blockers.append("amount_not_positive")

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            if "discard_deleted" in blockers:
                route = "discard_deleted_source"
            elif "supplier_contract_anchor_missing" in blockers:
                route = "block_supplier_contract_anchor_missing"
            elif "amount_not_positive" in blockers:
                route = "block_amount_not_positive"
            else:
                route = "manual_review_hold"
            route_counts[route] += 1
        else:
            route = "loadable_candidate_amount_line"
            route_counts[route] += 1
            amount_source_counts[amount_source] += 1

        output_rows.append(
            {
                "legacy_supplier_contract_id": legacy_id,
                "contract_external_id": contract_external_id,
                "amount": str(amount),
                "amount_source": amount_source,
                "qty_source": clean(row.get("ZSL")),
                "price_source": clean(row.get("DJ")),
                "line_name_source": clean(row.get("CLMC")),
                "route": route,
                "blockers": ",".join(blockers),
            }
        )

    loadable = route_counts["loadable_candidate_amount_line"]
    payload = {
        "status": "PASS",
        "source_table": "T_GYSHT_INFO",
        "lane": "supplier_contract_line",
        "target_model_candidate": "construction.contract.line",
        "raw_rows": len(rows),
        "loadable_candidate_rows": loadable,
        "blocked_rows": len(rows) - loadable,
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "amount_source_counts": dict(sorted(amount_source_counts.items())),
        "required_facts": ["supplier_contract_anchor", "amount_positive"],
        "line_policy": "qty_contract=1 and price_contract=source positive amount unless later line-detail evidence is stronger",
        "boundary": "header_amount_not_written; construction.contract header totals must be computed from line facts",
        "decision": "supplier_contract line amount facts can proceed to carrier mapping and XML generation",
        "next_step": "freeze construction.contract.line carrier boundary and generate supplier_contract_line XML assets",
    }
    return payload, output_rows


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    amount_rows = "\n".join(f"| {source} | {count} |" for source, count in payload["amount_source_counts"].items())
    return f"""# Legacy Supplier Contract Line Screen v1

Status: `{payload["status"]}`

This is a read-only old-database screen for supplier contract amount facts
before construction.contract.line asset generation.

## Required Facts

- supplier_contract_anchor
- amount_positive

The target is `construction.contract.line`. The header amount is
`header_amount_not_written`; construction.contract header totals must be
computed from line facts.

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
        require(payload["loadable_candidate_rows"] > 0, "no supplier contract line candidates")
        require(OUTPUT_JSON.exists(), f"missing output: {OUTPUT_JSON}")
        require(OUTPUT_CSV.exists(), f"missing output: {OUTPUT_CSV}")
        require(OUTPUT_MD.exists(), f"missing output: {OUTPUT_MD}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy supplier contract line facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = run(Path(args.asset_root), args.check)
    except (SupplierContractLineScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("SUPPLIER_CONTRACT_LINE_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "SUPPLIER_CONTRACT_LINE_SCREEN="
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
