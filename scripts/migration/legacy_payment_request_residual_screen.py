#!/usr/bin/env python3
"""Screen legacy payment request residual rows after outflow assets."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RUNTIME_ROOT = Path(".runtime_artifacts/migration_assets/payment_request_residual_screen")
OUTPUT_JSON = RUNTIME_ROOT / "legacy_payment_request_residual_screen_v1.json"
OUTPUT_MD = Path("docs/migration_alignment/frozen/legacy_payment_request_residual_screen_v1.md")
EXPECTED_RAW_ROWS = 13646

SQL = r"""
SET NOCOUNT ON;
DECLARE @sep varchar(1) = '|';
SELECT CONCAT(
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), Id), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), DJBH), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_XMID), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_XMMC), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_GYSID), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_GYSMC), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_JHJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_JHFKJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_NEW_JHJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_SFJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), ZSJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), YJJE), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_SQRQ, 120), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), DJZT), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), DEL), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), SCRID), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), SCR), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), SCRQ, 120), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_GYSHTID), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), ''), @sep,
  ISNULL(REPLACE(REPLACE(REPLACE(CONVERT(nvarchar(max), f_Remark), @sep, ' '), CHAR(13), ' '), CHAR(10), ' '), '')
) AS rowdata
FROM dbo.C_ZFSQGL
ORDER BY Id;
"""

SQL_COLUMNS = [
    "legacy_id", "document_no", "project_id", "project_name", "partner_id", "partner_name",
    "f_JHJE", "f_JHFKJE", "f_NEW_JHJE", "f_SFJE", "ZSJE", "YJJE",
    "document_date", "state", "deleted", "deleted_by_id", "deleted_by", "deleted_at",
    "contract_id", "note",
]
AMOUNT_FIELDS = ("f_JHJE", "f_JHFKJE", "f_NEW_JHJE", "f_SFJE", "ZSJE", "YJJE")


class PaymentRequestResidualScreenError(Exception):
    pass


def clean(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.upper() == "NULL" else text


def require(condition: bool, message: str) -> None:
    if not condition:
        raise PaymentRequestResidualScreenError(message)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    require(path.exists(), f"missing json file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_amount(value: str) -> Decimal:
    try:
        return Decimal(clean(value) or "0")
    except InvalidOperation:
        return Decimal("0")


def best_amount(row: dict[str, str]) -> tuple[str, Decimal]:
    for field in AMOUNT_FIELDS:
        amount = parse_amount(row.get(field, ""))
        if amount > 0:
            return field, amount
    return "", Decimal("0")


def run_sql() -> str:
    cmd = ["docker", "exec", "-i", "legacy-sqlserver", "bash", "-lc", "/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P \"$SA_PASSWORD\" -C -d LegacyDb -s '|' -y 0 -Y 0"]
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
    require(len(rows) == EXPECTED_RAW_ROWS, f"payment request raw row count drifted: {len(rows)} != {EXPECTED_RAW_ROWS}")
    return rows


def load_project_refs(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/project_external_id_manifest_v1.json")
    refs = set()
    for row in manifest.get("records", []):
        if row.get("status") == "loadable":
            refs.add(clean(row.get("legacy_key")))
            refs.add(clean((row.get("target_lookup") or {}).get("value")))
    refs.discard("")
    return refs


def load_partner_refs(asset_root: Path) -> set[str]:
    refs: set[str] = set()
    for rel_path in ("manifest/partner_external_id_manifest_v1.json", "manifest/receipt_counterparty_partner_external_id_manifest_v1.json", "manifest/contract_counterparty_partner_external_id_manifest_v1.json"):
        path = asset_root / rel_path
        if not path.exists():
            continue
        manifest = load_json(path)
        for row in manifest.get("records", []):
            if row.get("status") == "loadable":
                refs.add(clean(row.get("legacy_partner_id")))
    refs.discard("")
    return refs


def load_existing_outflows(asset_root: Path) -> set[str]:
    manifest = load_json(asset_root / "manifest/outflow_request_external_id_manifest_v1.json")
    return {
        clean(row.get("legacy_outflow_id"))
        for row in manifest.get("records", [])
        if row.get("status") == "loadable" and clean(row.get("legacy_outflow_id"))
    }


def is_deleted(row: dict[str, str]) -> bool:
    return clean(row.get("deleted")) == "1" or bool(clean(row.get("deleted_by_id")) or clean(row.get("deleted_by")) or clean(row.get("deleted_at")))


def classify_row(row: dict[str, str], project_refs: set[str], partner_refs: set[str], existing: set[str]) -> tuple[str, list[str]]:
    legacy_id = clean(row.get("legacy_id"))
    if legacy_id in existing:
        return "already_assetized_outflow", []
    reasons: list[str] = []
    if not legacy_id:
        reasons.append("missing_legacy_id")
    if is_deleted(row):
        reasons.append("deleted")
    project_id = clean(row.get("project_id"))
    if not project_id:
        reasons.append("missing_project_id")
    elif project_id not in project_refs:
        reasons.append("project_not_assetized")
    partner_id = clean(row.get("partner_id"))
    if not partner_id:
        reasons.append("missing_partner_id")
    elif partner_id not in partner_refs:
        reasons.append("partner_not_assetized")
    if best_amount(row)[1] <= 0:
        reasons.append("amount_not_positive_or_missing")
    return ("residual_loadable_candidate" if not reasons else "blocked", reasons)


def screen(asset_root: Path) -> dict[str, Any]:
    rows = parse_sql_rows(run_sql())
    project_refs = load_project_refs(asset_root)
    partner_refs = load_partner_refs(asset_root)
    existing = load_existing_outflows(asset_root)
    routes: Counter[str] = Counter()
    reasons: Counter[str] = Counter()
    amount_sources: Counter[str] = Counter()
    partner_counts: Counter[str] = Counter()
    samples: dict[str, list[dict[str, str]]] = {"already_assetized_outflow": [], "residual_loadable_candidate": [], "blocked": []}
    for row in rows:
        route, blocked_reasons = classify_row(row, project_refs, partner_refs, existing)
        routes[route] += 1
        amount_field, amount = best_amount(row)
        if route == "residual_loadable_candidate":
            amount_sources[amount_field] += 1
        for reason in blocked_reasons:
            reasons[reason] += 1
        partner_id = clean(row.get("partner_id"))
        if partner_id and partner_id in partner_refs:
            partner_counts["partner_id_assetized"] += 1
        elif partner_id:
            partner_counts["partner_id_not_assetized"] += 1
        else:
            partner_counts["partner_missing"] += 1
        if len(samples[route]) < 20:
            samples[route].append({
                "legacy_id": clean(row.get("legacy_id")),
                "document_no": clean(row.get("document_no")),
                "project_id": clean(row.get("project_id")),
                "partner_id": partner_id,
                "partner_name": clean(row.get("partner_name")),
                "amount": str(amount),
                "amount_field": amount_field,
                "reasons": ",".join(blocked_reasons),
            })
    decision = "no_additional_payment_request_assetization_needed" if routes["residual_loadable_candidate"] == 0 else "open_payment_request_residual_assetization_lane"
    return {
        "status": "PASS",
        "raw_rows": len(rows),
        "already_assetized_rows": routes["already_assetized_outflow"],
        "residual_loadable_rows": routes["residual_loadable_candidate"],
        "blocked_rows": routes["blocked"],
        "route_counts": dict(routes),
        "blocked_reason_counts": dict(reasons.most_common()),
        "amount_source_counts": dict(amount_sources.most_common()),
        "partner_anchor_counts": dict(partner_counts.most_common()),
        "samples": samples,
        "decision": decision,
        "db_writes": 0,
        "odoo_shell": False,
    }


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Legacy Payment Request Residual Screen v1",
        "",
        "Status: `PASS`",
        "",
        "This is a read-only screen for `C_ZFSQGL` rows not covered by `outflow_request_sc_v1`.",
        "",
        "## Result",
        "",
        f"- raw rows: `{result['raw_rows']}`",
        f"- already assetized rows: `{result['already_assetized_rows']}`",
        f"- residual loadable rows: `{result['residual_loadable_rows']}`",
        f"- blocked rows: `{result['blocked_rows']}`",
        f"- decision: `{result['decision']}`",
        "- DB writes: `0`",
        "- Odoo shell: `false`",
        "",
        "## Blocked Reasons",
        "",
        "| Reason | Rows |",
        "|---|---:|",
    ]
    for reason, count in result["blocked_reason_counts"].items():
        lines.append(f"| {reason} | {count} |")
    lines.extend(["", "## Partner Evidence", "", "| Route | Rows |", "|---|---:|"])
    for route, count in result["partner_anchor_counts"].items():
        lines.append(f"| {route} | {count} |")
    lines.extend(["", "## Decision", "", f"`{result['decision']}`", "", "## Boundary", "", "This screen does not generate `payment.request` or change existing outflow assets."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Screen legacy payment request residual rows.")
    parser.add_argument("--asset-root", default="migration_assets")
    parser.add_argument("--output-json", default=str(OUTPUT_JSON))
    parser.add_argument("--output-md", default=str(OUTPUT_MD))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        result = screen(Path(args.asset_root))
        write_json(Path(args.output_json), result)
        write_report(Path(args.output_md), result)
    except (PaymentRequestResidualScreenError, json.JSONDecodeError) as exc:
        payload = {"status": "FAIL", "error": str(exc), "db_writes": 0, "odoo_shell": False}
        print("LEGACY_PAYMENT_REQUEST_RESIDUAL_SCREEN=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))
        return 1 if args.check else 0
    print("LEGACY_PAYMENT_REQUEST_RESIDUAL_SCREEN=" + json.dumps({
        "status": "PASS",
        "raw_rows": result["raw_rows"],
        "already_assetized_rows": result["already_assetized_rows"],
        "residual_loadable_rows": result["residual_loadable_rows"],
        "blocked_rows": result["blocked_rows"],
        "decision": result["decision"],
        "db_writes": 0,
        "odoo_shell": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
