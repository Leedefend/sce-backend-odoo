#!/usr/bin/env python3
"""Screen legacy supplier contract facts before asset generation."""

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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_supplier_contract_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_supplier_contract_fact_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "legacy_supplier_contract_fact_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_supplier_contract_fact_screen_v1.md")
EXPECTED_RAW_ROWS = 5535

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), XMID) AS XMID,
  CONVERT(nvarchar(max), TSXMID) AS TSXMID,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), f_HTBH) AS f_HTBH,
  CONVERT(nvarchar(max), f_GYSID) AS f_GYSID,
  CONVERT(nvarchar(max), f_GYSName) AS f_GYSName,
  CONVERT(nvarchar(max), f_QYRQ, 120) AS f_QYRQ,
  CONVERT(nvarchar(max), f_ZT) AS f_ZT,
  CONVERT(nvarchar(max), DJZT) AS DJZT,
  CONVERT(nvarchar(max), ZJE) AS ZJE,
  CONVERT(nvarchar(max), ZJE_NO) AS ZJE_NO,
  CONVERT(nvarchar(max), HTLX) AS HTLX,
  CONVERT(nvarchar(max), HTLX_New) AS HTLX_New,
  CONVERT(nvarchar(max), HTMC) AS HTMC,
  CONVERT(nvarchar(max), DEL) AS DEL,
  CONVERT(nvarchar(max), SCRID) AS SCRID,
  CONVERT(nvarchar(max), SCR) AS SCR,
  CONVERT(nvarchar(max), SCRQ, 120) AS SCRQ
FROM dbo.T_GYSHT_INFO
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(XMID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(TSXMID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_HTBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_GYSID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_GYSName, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_QYRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(f_ZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJZT, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZJE_NO, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTLX, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTLX_New, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(HTMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DEL, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCR, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SCRQ, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = [
    "Id",
    "XMID",
    "TSXMID",
    "DJBH",
    "f_HTBH",
    "f_GYSID",
    "f_GYSName",
    "f_QYRQ",
    "f_ZT",
    "DJZT",
    "ZJE",
    "ZJE_NO",
    "HTLX",
    "HTLX_New",
    "HTMC",
    "DEL",
    "SCRID",
    "SCR",
    "SCRQ",
]


class SupplierContractFactScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SupplierContractFactScreenError(message)


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


def build_project_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("target_lookup", {}).get("value"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "project external id map is empty")
    return result


def build_partner_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_partner_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    return result


def merge_maps(*maps: dict[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for mapping in maps:
        for key, value in mapping.items():
            result.setdefault(key, value)
    require(result, "merged partner map is empty")
    return result


def parse_amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def first_nonempty(row: dict[str, str], fields: list[str]) -> str:
    for field in fields:
        value = clean(row.get(field))
        if value:
            return value
    return ""


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("DEL")) == "1" or bool(clean(row.get("SCRID")) or clean(row.get("SCR")) or clean(row.get("SCRQ")))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_supplier_contract_id",
        "legacy_project_id",
        "legacy_partner_id",
        "contract_no",
        "document_no",
        "amount",
        "project_resolved",
        "partner_resolved",
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
    project_by_legacy = build_project_map(load_json(asset_root / "manifest/project_external_id_manifest_v1.json"))
    partner_by_legacy = merge_maps(
        build_partner_map(load_json(asset_root / "manifest/partner_external_id_manifest_v1.json")),
        build_partner_map(load_json(asset_root / "manifest/contract_counterparty_partner_external_id_manifest_v1.json")),
        build_partner_map(load_json(asset_root / "manifest/receipt_counterparty_partner_external_id_manifest_v1.json")),
    )

    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    amount_policy_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        legacy_id = clean(row.get("Id"))
        legacy_project_id = first_nonempty(row, ["XMID", "TSXMID"])
        legacy_partner_id = clean(row.get("f_GYSID"))
        contract_no = first_nonempty(row, ["f_HTBH", "CGHTBH", "DJBH"])
        document_no = clean(row.get("DJBH"))
        amount = parse_amount(row.get("ZJE")) or parse_amount(row.get("ZJE_NO"))
        project_resolved = bool(project_by_legacy.get(legacy_project_id))
        partner_resolved = bool(partner_by_legacy.get(legacy_partner_id))
        status_counts[clean(row.get("f_ZT")) or "blank"] += 1

        blockers: list[str] = []
        if not legacy_id:
            blockers.append("missing_legacy_supplier_contract_id")
        if is_deleted(row):
            blockers.append("discard_deleted")
        if not contract_no:
            blockers.append("missing_contract_identity")
        if not project_resolved:
            blockers.append("project_not_in_asset")
        if not legacy_partner_id:
            blockers.append("missing_partner_ref")
        elif not partner_resolved:
            blockers.append("partner_not_in_asset")

        if amount > 0:
            amount_policy_counts["amount_positive"] += 1
        else:
            amount_policy_counts["amount_optional_blank_or_zero"] += 1

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            if "discard_deleted" in blockers:
                route = "discard_deleted_source"
            elif "missing_contract_identity" in blockers:
                route = "block_contract_identity_missing"
            elif "project_not_in_asset" in blockers:
                route = "block_project_anchor_missing"
            elif "missing_partner_ref" in blockers or "partner_not_in_asset" in blockers:
                route = "block_partner_anchor_missing"
            else:
                route = "manual_review_hold"
            route_counts[route] += 1
        else:
            route = "loadable_candidate_amount_optional"
            route_counts[route] += 1

        output_rows.append(
            {
                "legacy_supplier_contract_id": legacy_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "contract_no": contract_no,
                "document_no": document_no,
                "amount": str(amount),
                "project_resolved": project_resolved,
                "partner_resolved": partner_resolved,
                "route": route,
                "blockers": ",".join(blockers),
            }
        )

    loadable = route_counts["loadable_candidate_amount_optional"]
    blocked = len(rows) - loadable
    payload = {
        "status": "PASS",
        "source_table": "T_GYSHT_INFO",
        "lane": "supplier_contract",
        "target_model_candidate": "construction.contract",
        "raw_rows": len(rows),
        "loadable_candidate_rows": loadable,
        "blocked_rows": blocked,
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "amount_policy_counts": dict(sorted(amount_policy_counts.items())),
        "status_counts": dict(sorted(status_counts.items())),
        "required_facts": [
            "stable supplier contract source id",
            "contract identity",
            "project anchor",
            "partner anchor",
        ],
        "optional_facts": ["amount", "contract date", "contract status text"],
        "decision": (
            "supplier_contract facts can proceed to carrier mapping. amount_optional "
            "is required because the target contract header does not require amount "
            "and summary amount must not be fabricated."
        ),
        "next_step": "screen target construction.contract carrier fields for supplier_contract XML asset generation",
    }
    return payload, output_rows


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {route} | {count} |" for route, count in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {blocker} | {count} |" for blocker, count in payload["blocker_counts"].items())
    amount_rows = "\n".join(f"| {policy} | {count} |" for policy, count in payload["amount_policy_counts"].items())
    return f"""# Legacy Supplier Contract Fact Screen v1

Status: `{payload["status"]}`

This is a read-only old-database screen for `supplier_contract` facts before
asset generation. It performs no DB write and does not generate XML assets.

## Required Facts

- stable supplier contract source id
- contract identity
- project_anchor
- partner_anchor

Amount is `amount_optional`: it may be preserved when positive, but it must not
block contract header assetization and must not be fabricated.

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

## Amount Policy

| Policy | Rows |
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
        require(payload["loadable_candidate_rows"] > 0, "no supplier contract candidates")
        require(OUTPUT_JSON.exists(), f"missing output: {OUTPUT_JSON}")
        require(OUTPUT_CSV.exists(), f"missing output: {OUTPUT_CSV}")
        require(OUTPUT_MD.exists(), f"missing output: {OUTPUT_MD}")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy supplier contract facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        payload = run(Path(args.asset_root), args.check)
    except (SupplierContractFactScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("SUPPLIER_CONTRACT_FACT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "SUPPLIER_CONTRACT_FACT_SCREEN="
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
