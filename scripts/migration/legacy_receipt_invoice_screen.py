#!/usr/bin/env python3
"""Screen legacy receipt invoice line facts before carrier selection."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


REPO_ASSET_ROOT = Path("migration_assets")
RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/legacy_receipt_invoice_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_receipt_invoice_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_receipt_invoice_screen_v1.md")
EXPECTED_RAW_ROWS = 4491

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
WITH src AS (
SELECT
  CONVERT(nvarchar(max), Id) AS Id,
  CONVERT(nvarchar(max), ZBID) AS ZBID,
  CONVERT(nvarchar(max), FPHM) AS FPHM,
  CONVERT(nvarchar(max), SPFMC) AS SPFMC,
  CONVERT(nvarchar(max), KPJE) AS KPJE,
  CONVERT(nvarchar(max), CCSKJE) AS CCSKJE,
  CONVERT(nvarchar(max), YKPJE) AS YKPJE,
  CONVERT(nvarchar(max), FPID) AS FPID,
  CONVERT(nvarchar(max), DJBH) AS DJBH,
  CONVERT(nvarchar(max), KPDW) AS KPDW,
  CONVERT(nvarchar(max), FP_CB_Id) AS FP_CB_Id,
  CONVERT(nvarchar(max), pid) AS pid
FROM dbo.C_JFHKLR_CB
)
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(ZBID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPHM, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(SPFMC, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(KPJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CCSKJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(YKPJE, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FPID, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(DJBH, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(KPDW, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(FP_CB_Id, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(pid, @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM src
ORDER BY Id;
"""

SQL_COLUMNS = ["Id", "ZBID", "FPHM", "SPFMC", "KPJE", "CCSKJE", "YKPJE", "FPID", "DJBH", "KPDW", "FP_CB_Id", "pid"]


class ReceiptInvoiceScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReceiptInvoiceScreenError(message)


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


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


def receipt_map(asset_root: Path) -> dict[str, str]:
    manifest = load_json(asset_root / "manifest/receipt_external_id_manifest_v1.json")
    result: dict[str, str] = {}
    for row in manifest.get("records", []):
        legacy_id = clean(row.get("legacy_receipt_id"))
        external_id = clean(row.get("external_id"))
        if legacy_id and external_id and row.get("status") == "loadable":
            result[legacy_id] = external_id
    require(result, "receipt external id map is empty")
    return result


def amount(value: object) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in ("KPJE", "CCSKJE", "YKPJE"):
        value = amount(row.get(field))
        if value > 0:
            return field, value
    return "", Decimal("0")


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    receipt_by_legacy = receipt_map(asset_root)
    routes: Counter[str] = Counter()
    blockers: Counter[str] = Counter()
    amount_sources: Counter[str] = Counter()
    invoice_no_counts: Counter[str] = Counter()

    for row in rows:
        legacy_line_id = clean(row.get("Id"))
        legacy_receipt_id = clean(row.get("ZBID"))
        receipt_external_id = receipt_by_legacy.get(legacy_receipt_id, "")
        amount_source, invoice_amount = best_amount(row)
        row_blockers: list[str] = []
        if not legacy_line_id:
            row_blockers.append("missing_legacy_receipt_invoice_line_id")
        if not legacy_receipt_id:
            row_blockers.append("missing_parent_receipt_id")
        elif not receipt_external_id:
            row_blockers.append("receipt_anchor_missing")
        if invoice_amount <= 0:
            row_blockers.append("amount_not_positive")
        if clean(row.get("FPHM")):
            invoice_no_counts["invoice_no_present"] += 1
        else:
            invoice_no_counts["invoice_no_empty"] += 1
        if row_blockers:
            for blocker in row_blockers:
                blockers[blocker] += 1
            if "receipt_anchor_missing" in row_blockers or "missing_parent_receipt_id" in row_blockers:
                routes["block_receipt_anchor_missing"] += 1
            elif "amount_not_positive" in row_blockers:
                routes["block_amount_not_positive"] += 1
            else:
                routes["manual_review_hold"] += 1
        else:
            routes["loadable_candidate_invoice_fact"] += 1
            amount_sources[amount_source] += 1

    loadable = routes["loadable_candidate_invoice_fact"]
    return {
        "status": "PASS",
        "source_table": "C_JFHKLR_CB",
        "lane": "receipt_invoice",
        "raw_rows": len(rows),
        "loadable_candidate_rows": loadable,
        "blocked_rows": len(rows) - loadable,
        "route_counts": dict(sorted(routes.items())),
        "blocker_counts": dict(sorted(blockers.items())),
        "amount_source_counts": dict(sorted(amount_sources.items())),
        "invoice_no_counts": dict(sorted(invoice_no_counts.items())),
        "carrier_decision": "no_safe_existing_xml_carrier",
        "rejected_carriers": {
            "account.move": "accounting truth and posting semantics; forbidden for auxiliary receipt invoice facts",
            "sc.settlement.order.invoice_*": "header placeholder fields; cannot preserve multiple invoice lines per receipt",
            "payment.request.note": "unstructured text cannot provide replayable line facts",
        },
        "next_step": "new_receipt_invoice_line_carrier_required",
        "db_writes": 0,
        "odoo_shell": False,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    route_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["route_counts"].items())
    blocker_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["blocker_counts"].items())
    amount_rows = "\n".join(f"| {key} | {value} |" for key, value in payload["amount_source_counts"].items())
    return f"""# Legacy Receipt Invoice Screen v1

Status: `{payload["status"]}`

This is a read-only screen for legacy receipt invoice line facts before XML
asset generation.

## Result

- source table: `{payload["source_table"]}`
- raw rows: `{payload["raw_rows"]}`
- loadable candidates: `{payload["loadable_candidate_rows"]}`
- blocked rows: `{payload["blocked_rows"]}`
- carrier decision: `{payload["carrier_decision"]}`
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

## Rejected Carriers

- `account.move`: {payload["rejected_carriers"]["account.move"]}
- `sc.settlement.order.invoice_*`: {payload["rejected_carriers"]["sc.settlement.order.invoice_*"]}
- `payment.request.note`: {payload["rejected_carriers"]["payment.request.note"]}

## Decision

`new_receipt_invoice_line_carrier_required`
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy receipt invoice facts.")
    parser.add_argument("--asset-root", default=str(REPO_ASSET_ROOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        payload = screen(Path(args.asset_root))
        OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_MD.write_text(render_markdown(payload), encoding="utf-8")
        if args.check:
            require(payload["raw_rows"] == EXPECTED_RAW_ROWS, "raw row count mismatch")
            require(payload["loadable_candidate_rows"] > 0, "no loadable invoice candidates")
            require(payload["carrier_decision"] == "no_safe_existing_xml_carrier", "carrier decision drift")
    except (ReceiptInvoiceScreenError, json.JSONDecodeError) as exc:
        result = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("RECEIPT_INVOICE_SCREEN=" + json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print(
        "RECEIPT_INVOICE_SCREEN="
        + json.dumps(
            {
                "status": payload["status"],
                "raw_rows": payload["raw_rows"],
                "loadable_candidate_rows": payload["loadable_candidate_rows"],
                "blocked_rows": payload["blocked_rows"],
                "carrier_decision": payload["carrier_decision"],
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
