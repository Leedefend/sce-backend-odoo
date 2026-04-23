#!/usr/bin/env python3
"""Screen legacy actual outflow facts before asset generation."""

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
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_actual_outflow_fact_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_actual_outflow_fact_screen_v1.json"
OUTPUT_CSV = RUNTIME_ROOT / "legacy_actual_outflow_fact_screen_rows_v1.csv"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_actual_outflow_fact_screen_v1.md")
EXPECTED_RAW_ROWS = 13629

SQL = r"""
SET NOCOUNT ON;
SELECT
  Id,
  f_XMID,
  f_LYXMID,
  TSXMID,
  f_SupplierID,
  f_HTID,
  f_ZFSQGLId,
  f_FKJE,
  f_FKRQ,
  DJBH,
  DEL,
  f_SupplierName,
  f_HTHB,
  ZFSQDH
FROM dbo.T_FK_Supplier
ORDER BY Id;
"""


class ActualOutflowFactScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ActualOutflowFactScreenError(message)


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
    reader = csv.reader(output.splitlines(), delimiter="|")
    header: list[str] | None = None
    for raw_parts in reader:
        parts = [part.strip() for part in raw_parts]
        if not parts or len(parts) < 2:
            continue
        if parts[0] == "Id":
            header = parts
            continue
        if header is None or len(parts) != len(header):
            continue
        if all(part and set(part) <= {"-"} for part in parts):
            continue
        rows.append(dict(zip(header, parts)))
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
    require(result, "merged map is empty")
    return result


def build_outflow_request_map(manifest: dict[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_outflow_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "outflow request external id map is empty")
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
    return clean(row.get("DEL")) == "1"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "legacy_actual_outflow_id",
        "legacy_project_id",
        "legacy_partner_id",
        "legacy_request_id",
        "legacy_supplier_contract_id",
        "amount",
        "project_resolved",
        "partner_resolved",
        "request_resolved",
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
    request_by_legacy = build_outflow_request_map(load_json(asset_root / "manifest/outflow_request_external_id_manifest_v1.json"))

    route_counts: Counter[str] = Counter()
    blocker_counts: Counter[str] = Counter()
    request_anchor_counts: Counter[str] = Counter()
    supplier_contract_counts: Counter[str] = Counter()
    output_rows: list[dict[str, Any]] = []

    for row in rows:
        legacy_id = clean(row.get("Id"))
        legacy_project_id = first_nonempty(row, ["f_XMID", "f_LYXMID", "TSXMID"])
        legacy_partner_id = clean(row.get("f_SupplierID"))
        legacy_request_id = clean(row.get("f_ZFSQGLId"))
        legacy_supplier_contract_id = clean(row.get("f_HTID"))
        amount = parse_amount(row.get("f_FKJE"))
        project_resolved = bool(project_by_legacy.get(legacy_project_id))
        partner_resolved = bool(partner_by_legacy.get(legacy_partner_id))
        request_resolved = bool(request_by_legacy.get(legacy_request_id)) if legacy_request_id else False

        blockers: list[str] = []
        if not legacy_id:
            blockers.append("missing_legacy_actual_outflow_id")
        if is_deleted(row):
            blockers.append("discard_deleted")
        if amount <= 0:
            blockers.append("zero_or_negative_amount")
        if not legacy_project_id:
            blockers.append("missing_project_ref")
        elif not project_resolved:
            blockers.append("project_not_in_asset")
        if not legacy_partner_id:
            blockers.append("missing_partner_ref")
        elif not partner_resolved:
            blockers.append("partner_not_in_asset")

        if blockers:
            for blocker in blockers:
                blocker_counts[blocker] += 1
            if "discard_deleted" in blockers:
                route = "discard_deleted_source"
            elif "zero_or_negative_amount" in blockers:
                route = "discard_non_positive_amount"
            elif "missing_project_ref" in blockers or "project_not_in_asset" in blockers:
                route = "block_project_anchor_missing"
            elif "missing_partner_ref" in blockers or "partner_not_in_asset" in blockers:
                route = "block_partner_anchor_missing"
            else:
                route = "manual_review_hold"
        else:
            request_anchor_counts["request_resolved" if request_resolved else ("request_unresolved" if legacy_request_id else "request_empty")] += 1
            supplier_contract_counts["supplier_contract_present" if legacy_supplier_contract_id else "supplier_contract_empty"] += 1
            route = "loadable_candidate_request_optional"
        route_counts[route] += 1

        output_rows.append(
            {
                "legacy_actual_outflow_id": legacy_id,
                "legacy_project_id": legacy_project_id,
                "legacy_partner_id": legacy_partner_id,
                "legacy_request_id": legacy_request_id,
                "legacy_supplier_contract_id": legacy_supplier_contract_id,
                "amount": str(amount),
                "project_resolved": "1" if project_resolved else "0",
                "partner_resolved": "1" if partner_resolved else "0",
                "request_resolved": "1" if request_resolved else "0",
                "route": route,
                "blockers": ",".join(blockers),
            }
        )

    loadable = route_counts["loadable_candidate_request_optional"]
    payload = {
        "status": "PASS",
        "mode": "legacy_actual_outflow_fact_screen",
        "source": "legacy-sqlserver:LegacyDb.dbo.T_FK_Supplier",
        "raw_rows": len(rows),
        "loadable_candidate_rows": loadable,
        "blocked_rows": len(rows) - loadable,
        "route_counts": dict(sorted(route_counts.items())),
        "blocker_counts": dict(sorted(blocker_counts.items())),
        "request_anchor_counts": dict(sorted(request_anchor_counts.items())),
        "supplier_contract_counts": dict(sorted(supplier_contract_counts.items())),
        "row_artifact": str(OUTPUT_CSV),
        "db_writes": 0,
        "odoo_shell": False,
        "decision": "actual_outflow_screen_pass_asset_generation_next_after_owner_accepts_contract_optional_policy",
        "next_step": "Generate actual outflow assets with optional outflow_request_id and deferred supplier_contract_id, or first assetize supplier contracts if contract anchoring must be mandatory.",
    }
    return payload, output_rows


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["blocker_counts"].items())
    request_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["request_anchor_counts"].items())
    contract_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["supplier_contract_counts"].items())
    return f"""# Legacy Actual Outflow Fact Screen v1

Status: `{payload["status"]}`

Source: `{payload["source"]}`

This is a direct legacy database, read-only screen for actual outflow facts.
It checks project_anchor, partner_anchor, positive amount, stable row id, and
optional outflow request_anchor against repository migration assets.

## Result

- raw rows: `{payload["raw_rows"]}`
- loadable candidates: `{payload["loadable_candidate_rows"]}`
- blocked/discarded rows: `{payload["blocked_rows"]}`
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

## Request Anchor

| request_anchor | Rows |
|---|---:|
{request_rows}

## Supplier Contract Presence

| supplier_contract | Rows |
|---|---:|
{contract_rows}

## Decision

`{payload["decision"]}`

## Next

{payload["next_step"]}
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy actual outflow facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload, rows = screen(Path(args.asset_root))
        write_json(OUTPUT_JSON, payload)
        write_csv(OUTPUT_CSV, rows)
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
    except (ActualOutflowFactScreenError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_ACTUAL_OUTFLOW_FACT_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0

    print(
        "LEGACY_ACTUAL_OUTFLOW_FACT_SCREEN="
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
